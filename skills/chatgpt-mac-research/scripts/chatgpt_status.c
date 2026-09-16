#include <ApplicationServices/ApplicationServices.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <time.h>

#define BUF_SIZE 131072

typedef struct {
    int stop_button_count;
    int send_button_count;
    int dictate_button_count;
    int copy_button_count;
    int total_elements;
} UIState;

typedef struct {
    char markdown[BUF_SIZE];
    int len;
    bool in_assistant;
} MDBuilder;

static void md_append(MDBuilder *b, const char *str) {
    int slen = strlen(str);
    if (b->len + slen < BUF_SIZE - 2) {
        memcpy(b->markdown + b->len, str, slen);
        b->len += slen;
        b->markdown[b->len] = '\0';
    }
}

// Collect all text recursively within a single block, joining inline spans cleanly
static void collect_block_text(AXUIElementRef el, int depth, char *buf, int *buf_len, int max_len) {
    if (depth > 25 || *buf_len >= max_len - 1) return;

    CFTypeRef role = NULL;
    char role_str[64] = "";
    if (AXUIElementCopyAttributeValue(el, kAXRoleAttribute, &role) == kAXErrorSuccess && role) {
        if (CFGetTypeID(role) == CFStringGetTypeID()) {
            CFStringGetCString((CFStringRef)role, role_str, sizeof(role_str), kCFStringEncodingUTF8);
        }
        CFRelease(role);
    }

    if (strcmp(role_str, "AXStaticText") == 0) {
        CFTypeRef val = NULL;
        if (AXUIElementCopyAttributeValue(el, kAXValueAttribute, &val) == kAXErrorSuccess && val) {
            if (CFGetTypeID(val) == CFStringGetTypeID()) {
                char str[4096];
                if (CFStringGetCString((CFStringRef)val, str, sizeof(str), kCFStringEncodingUTF8)) {
                    int slen = strlen(str);
                    if (*buf_len + slen < max_len - 1) {
                        memcpy(buf + *buf_len, str, slen);
                        *buf_len += slen;
                        buf[*buf_len] = '\0';
                    }
                }
            }
            CFRelease(val);
        }
        return;
    }

    CFArrayRef children = NULL;
    if (AXUIElementCopyAttributeValue(el, kAXChildrenAttribute, (CFTypeRef *)&children) == kAXErrorSuccess && children) {
        CFIndex count = CFArrayGetCount(children);
        for (CFIndex i = 0; i < count; i++) {
            AXUIElementRef child = (AXUIElementRef)CFArrayGetValueAtIndex(children, i);
            collect_block_text(child, depth + 1, buf, buf_len, max_len);
        }
        CFRelease(children);
    }
}

static void parse_message_blocks(AXUIElementRef el, int depth, MDBuilder *b) {
    if (depth > 40) return;

    CFTypeRef role = NULL;
    char role_str[64] = "";
    if (AXUIElementCopyAttributeValue(el, kAXRoleAttribute, &role) == kAXErrorSuccess && role) {
        if (CFGetTypeID(role) == CFStringGetTypeID()) {
            CFStringGetCString((CFStringRef)role, role_str, sizeof(role_str), kCFStringEncodingUTF8);
        }
        CFRelease(role);
    }

    CFTypeRef subrole = NULL;
    char subrole_str[64] = "";
    if (AXUIElementCopyAttributeValue(el, kAXSubroleAttribute, &subrole) == kAXErrorSuccess && subrole) {
        if (CFGetTypeID(subrole) == CFStringGetTypeID()) {
            CFStringGetCString((CFStringRef)subrole, subrole_str, sizeof(subrole_str), kCFStringEncodingUTF8);
        }
        CFRelease(subrole);
    }

    // Detect transition to assistant message
    if (!b->in_assistant && strcmp(role_str, "AXStaticText") == 0) {
        CFTypeRef val = NULL;
        if (AXUIElementCopyAttributeValue(el, kAXValueAttribute, &val) == kAXErrorSuccess && val) {
            if (CFGetTypeID(val) == CFStringGetTypeID()) {
                char str[256];
                if (CFStringGetCString((CFStringRef)val, str, sizeof(str), kCFStringEncodingUTF8)) {
                    if (strcmp(str, "ChatGPT said:") == 0) {
                        b->in_assistant = true;
                        b->len = 0;
                        b->markdown[0] = '\0';
                        CFRelease(val);
                        return;
                    }
                }
            }
            CFRelease(val);
        }
    }

    if (!b->in_assistant) {
        CFArrayRef children = NULL;
        if (AXUIElementCopyAttributeValue(el, kAXChildrenAttribute, (CFTypeRef *)&children) == kAXErrorSuccess && children) {
            CFIndex count = CFArrayGetCount(children);
            for (CFIndex i = 0; i < count; i++) {
                parse_message_blocks((AXUIElementRef)CFArrayGetValueAtIndex(children, i), depth + 1, b);
            }
            CFRelease(children);
        }
        return;
    }

    // Inside assistant response
    if (strcmp(role_str, "AXHeading") == 0) {
        char text[4096] = "";
        int tlen = 0;
        collect_block_text(el, 0, text, &tlen, sizeof(text));
        if (tlen > 0 && 
            strcmp(text, "Suspicious activity detected") != 0 &&
            strncmp(text, "Security", 8) != 0 &&
            strcmp(text, "ChatGPT can make mistakes. Check important info.") != 0) {
            md_append(b, "### ");
            md_append(b, text);
            md_append(b, "\n\n");
        }
        return;
    }

    if (strcmp(subrole_str, "AXCodeStyleGroup") == 0) {
        char text[8192] = "";
        int tlen = 0;
        collect_block_text(el, 0, text, &tlen, sizeof(text));
        if (tlen > 0) {
            md_append(b, "```\n");
            md_append(b, text);
            md_append(b, "\n```\n\n");
        }
        return;
    }

    if (strcmp(role_str, "AXList") == 0) {
        CFArrayRef items = NULL;
        if (AXUIElementCopyAttributeValue(el, kAXChildrenAttribute, (CFTypeRef *)&items) == kAXErrorSuccess && items) {
            CFIndex n = CFArrayGetCount(items);
            for (CFIndex i = 0; i < n; i++) {
                AXUIElementRef item = (AXUIElementRef)CFArrayGetValueAtIndex(items, i);
                char item_text[4096] = "";
                int itlen = 0;
                collect_block_text(item, 0, item_text, &itlen, sizeof(item_text));
                if (itlen > 0) {
                    md_append(b, "- ");
                    md_append(b, item_text);
                    md_append(b, "\n");
                }
            }
            md_append(b, "\n");
            CFRelease(items);
        }
        return;
    }

    if (strcmp(role_str, "AXParagraph") == 0) {
        char text[4096] = "";
        int tlen = 0;
        collect_block_text(el, 0, text, &tlen, sizeof(text));
        if (tlen > 0 && strcmp(text, "ChatGPT can make mistakes. Check important info.") != 0) {
            md_append(b, text);
            md_append(b, "\n\n");
        }
        return;
    }

    CFArrayRef children = NULL;
    if (AXUIElementCopyAttributeValue(el, kAXChildrenAttribute, (CFTypeRef *)&children) == kAXErrorSuccess && children) {
        CFIndex count = CFArrayGetCount(children);
        for (CFIndex i = 0; i < count; i++) {
            parse_message_blocks((AXUIElementRef)CFArrayGetValueAtIndex(children, i), depth + 1, b);
        }
        CFRelease(children);
    }
}

static void inspect_status(AXUIElementRef element, int depth, UIState *state) {
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
            inspect_status(child, depth + 1, state);
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
            inspect_status(win, 0, out_state);
        }
        CFRelease(windows);
    }
    CFRelease(app);
    return true;
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

        MDBuilder b = {0};
        CFArrayRef windows = NULL;
        if (AXUIElementCopyAttributeValue(app, kAXWindowsAttribute, (CFTypeRef *)&windows) == kAXErrorSuccess && windows) {
            CFIndex win_count = CFArrayGetCount(windows);
            for (CFIndex i = 0; i < win_count; i++) {
                AXUIElementRef win = (AXUIElementRef)CFArrayGetValueAtIndex(windows, i);
                parse_message_blocks(win, 0, &b);
            }
            CFRelease(windows);
        }
        CFRelease(app);

        printf("%s\n", b.markdown);
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
