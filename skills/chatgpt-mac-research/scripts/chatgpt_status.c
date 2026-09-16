#include <ApplicationServices/ApplicationServices.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <time.h>

#define MAX_EXTRACTED_LINES 4096

typedef struct {
    int stop_button_count;
    int send_button_count;
    int dictate_button_count;
    int copy_button_count;
    int total_elements;
} UIState;

typedef struct {
    char *lines[MAX_EXTRACTED_LINES];
    int count;
} ExtractedText;

static void inspect_element(AXUIElementRef element, int depth, UIState *state) {
    if (depth > 35) return;
    state->total_elements++;

    CFTypeRef role_val = NULL;
    char role_str[64] = "";
    if (AXUIElementCopyAttributeValue(element, kAXRoleAttribute, &role_val) == kAXErrorSuccess && role_val) {
        if (CFGetTypeID(role_val) == CFStringGetTypeID()) {
            CFStringGetCString((CFStringRef)role_val, role_str, sizeof(role_str), kCFStringEncodingUTF8);
        }
        CFRelease(role_val);
    }

    if (strcmp(role_str, "AXButton") == 0) {
        CFTypeRef desc_val = NULL;
        if (AXUIElementCopyAttributeValue(element, kAXDescriptionAttribute, &desc_val) == kAXErrorSuccess && desc_val) {
            if (CFGetTypeID(desc_val) == CFStringGetTypeID()) {
                char desc_str[256];
                if (CFStringGetCString((CFStringRef)desc_val, desc_str, sizeof(desc_str), kCFStringEncodingUTF8)) {
                    if (strcasecmp(desc_str, "Stop generating") == 0 || 
                        strcasecmp(desc_str, "Stop streaming") == 0 ||
                        strcmp(desc_str, "Stop") == 0) {
                        state->stop_button_count++;
                    } else if (strcasecmp(desc_str, "Send") == 0) {
                        state->send_button_count++;
                    } else if (strcasecmp(desc_str, "Dictate") == 0) {
                        state->dictate_button_count++;
                    } else if (strcasecmp(desc_str, "Copy") == 0) {
                        state->copy_button_count++;
                    }
                }
            }
            CFRelease(desc_val);
        }
    }

    CFArrayRef children = NULL;
    if (AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, (CFTypeRef *)&children) == kAXErrorSuccess && children) {
        CFIndex count = CFArrayGetCount(children);
        for (CFIndex i = 0; i < count; i++) {
            AXUIElementRef child = (AXUIElementRef)CFArrayGetValueAtIndex(children, i);
            inspect_element(child, depth + 1, state);
        }
        CFRelease(children);
    }
}

static pid_t get_chatgpt_pid(void) {
    FILE *fp = popen("pgrep -x ChatGPT || pgrep -i chatgpt | head -1", "r");
    if (!fp) return 0;
    char pid_str[32] = {0};
    if (!fgets(pid_str, sizeof(pid_str), fp)) {
        pclose(fp);
        return 0;
    }
    pclose(fp);
    return (pid_t)atoi(pid_str);
}

static bool query_state(pid_t pid, UIState *out_state) {
    memset(out_state, 0, sizeof(UIState));
    AXUIElementRef app = AXUIElementCreateApplication(pid);
    if (!app) return false;

    CFBooleanRef true_val = kCFBooleanTrue;
    AXUIElementSetAttributeValue(app, CFSTR("AXEnhancedUserInterface"), true_val);

    CFArrayRef windows = NULL;
    if (AXUIElementCopyAttributeValue(app, kAXWindowsAttribute, (CFTypeRef *)&windows) == kAXErrorSuccess && windows) {
        CFIndex win_count = CFArrayGetCount(windows);
        for (CFIndex i = 0; i < win_count; i++) {
            AXUIElementRef win = (AXUIElementRef)CFArrayGetValueAtIndex(windows, i);
            inspect_element(win, 0, out_state);
        }
        CFRelease(windows);
    }
    CFRelease(app);
    return true;
}

static void collect_texts(AXUIElementRef element, int depth, ExtractedText *out) {
    if (depth > 35 || out->count >= MAX_EXTRACTED_LINES) return;

    CFTypeRef role_val = NULL;
    char role_str[64] = "";
    if (AXUIElementCopyAttributeValue(element, kAXRoleAttribute, &role_val) == kAXErrorSuccess && role_val) {
        if (CFGetTypeID(role_val) == CFStringGetTypeID()) {
            CFStringGetCString((CFStringRef)role_val, role_str, sizeof(role_str), kCFStringEncodingUTF8);
        }
        CFRelease(role_val);
    }

    if (strcmp(role_str, "AXStaticText") == 0) {
        CFTypeRef val = NULL;
        if (AXUIElementCopyAttributeValue(element, kAXValueAttribute, &val) == kAXErrorSuccess && val) {
            if (CFGetTypeID(val) == CFStringGetTypeID()) {
                char str[4096];
                if (CFStringGetCString((CFStringRef)val, str, sizeof(str), kCFStringEncodingUTF8)) {
                    if (strcmp(str, "ChatGPT can make mistakes. Check important info.") != 0 &&
                        strcmp(str, "Message ChatGPT") != 0 &&
                        strncmp(str, "Search", 6) != 0 &&
                        strncmp(str, "Dragging was", 12) != 0) {
                        out->lines[out->count++] = strdup(str);
                    }
                }
            }
            CFRelease(val);
        }
    }

    CFArrayRef children = NULL;
    if (AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, (CFTypeRef *)&children) == kAXErrorSuccess && children) {
        CFIndex count = CFArrayGetCount(children);
        for (CFIndex i = 0; i < count && out->count < MAX_EXTRACTED_LINES; i++) {
            AXUIElementRef child = (AXUIElementRef)CFArrayGetValueAtIndex(children, i);
            collect_texts(child, depth + 1, out);
        }
        CFRelease(children);
    }
}

int main(int argc, char **argv) {
    bool do_wait = false;
    bool do_extract = false;
    int timeout_sec = 180;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--wait") == 0) {
            do_wait = true;
            if (i + 1 < argc && argv[i + 1][0] != '-') {
                timeout_sec = atoi(argv[++i]);
                if (timeout_sec <= 0) timeout_sec = 180;
            }
        } else if (strcmp(argv[i], "--extract") == 0) {
            do_extract = true;
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            printf("Usage: chatgpt_status [--wait [timeout_sec]] [--extract]\n");
            return 0;
        }
    }

    pid_t pid = get_chatgpt_pid();
    if (pid <= 0) {
        printf("{\"state\": \"not_running\", \"generating\": false, \"ready\": false}\n");
        return 2;
    }

    if (do_extract) {
        AXUIElementRef app = AXUIElementCreateApplication(pid);
        if (!app) return 1;
        CFBooleanRef true_val = kCFBooleanTrue;
        AXUIElementSetAttributeValue(app, CFSTR("AXEnhancedUserInterface"), true_val);

        ExtractedText et = {0};
        CFArrayRef windows = NULL;
        if (AXUIElementCopyAttributeValue(app, kAXWindowsAttribute, (CFTypeRef *)&windows) == kAXErrorSuccess && windows) {
            CFIndex win_count = CFArrayGetCount(windows);
            for (CFIndex i = 0; i < win_count; i++) {
                AXUIElementRef win = (AXUIElementRef)CFArrayGetValueAtIndex(windows, i);
                collect_texts(win, 0, &et);
            }
            CFRelease(windows);
        }
        CFRelease(app);

        // Find the start of the latest assistant message
        int start_idx = 0;
        for (int i = 0; i < et.count; i++) {
            if (strcmp(et.lines[i], "ChatGPT said:") == 0) {
                start_idx = i + 1; // start right after "ChatGPT said:"
            }
        }

        // Print cleanly
        for (int i = start_idx; i < et.count; i++) {
            printf("%s\n", et.lines[i]);
            free(et.lines[i]);
        }
        return 0;
    }

    if (do_wait) {
        time_t start = time(NULL);
        bool saw_generating = false;
        while (time(NULL) - start < timeout_sec) {
            UIState s;
            if (query_state(pid, &s)) {
                bool is_generating = (s.stop_button_count > 0);
                bool is_ready = (s.send_button_count > 0 || s.dictate_button_count > 0) && !is_generating;

                if (is_generating) {
                    saw_generating = true;
                }

                if (saw_generating && is_ready) {
                    printf("{\"state\": \"idle\", \"generating\": false, \"ready\": true, \"elapsed_sec\": %ld}\n", (long)(time(NULL) - start));
                    return 0;
                }
                if (!saw_generating && is_ready && (time(NULL) - start > 4)) {
                    printf("{\"state\": \"idle\", \"generating\": false, \"ready\": true, \"elapsed_sec\": %ld}\n", (long)(time(NULL) - start));
                    return 0;
                }
            }
            usleep(1500000);
        }
        printf("{\"state\": \"timeout\", \"generating\": true, \"ready\": false, \"elapsed_sec\": %d}\n", timeout_sec);
        return 1;
    }

    UIState s;
    if (!query_state(pid, &s)) {
        printf("{\"state\": \"error\", \"generating\": false, \"ready\": false}\n");
        return 1;
    }

    bool is_generating = (s.stop_button_count > 0);
    bool is_ready = (s.send_button_count > 0 || s.dictate_button_count > 0) && !is_generating;
    const char *state = is_generating ? "generating" : (is_ready ? "idle" : "unknown");

    printf("{\"state\": \"%s\", \"generating\": %s, \"ready\": %s, \"stop_buttons\": %d, \"send_buttons\": %d, \"copy_buttons\": %d, \"elements\": %d}\n",
           state, is_generating ? "true" : "false", is_ready ? "true" : "false",
           s.stop_button_count, s.send_button_count, s.copy_button_count, s.total_elements);

    return 0;
}
