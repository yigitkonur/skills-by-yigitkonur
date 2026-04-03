# Image Upload With PhotosPicker And AsyncImage

## Use This When
- Building a profile image or photo upload feature with Convex file storage.
- Implementing the PhotosPicker to upload, compress, and display flow end-to-end.
- Displaying uploaded images reactively with AsyncImage.

## End-To-End Flow

1. User picks an image with `PhotosPicker`.
2. Load the image data from `PhotosPickerItem`.
3. Compress with `UIImage.jpegData(compressionQuality:)`.
4. Upload via the three-step flow (generate URL, POST bytes with `URLSession`, save storage ID).
5. Display with `AsyncImage` from the URL returned by `ctx.storage.getUrl()`.

## Server-Side: Image Storage Functions

```typescript
// convex/images.ts
import { userMutation, userQuery } from "./functions";
import { v } from "convex/values";

export const generateUploadUrl = userMutation({
  args: {},
  handler: async (ctx) => {
    return await ctx.storage.generateUploadUrl();
  },
});

export const saveProfileImage = userMutation({
  args: { storageId: v.id("_storage") },
  handler: async (ctx, args) => {
    const userId = ctx.user._id;
    await ctx.db.patch(userId, {
      profileImageId: args.storageId,
    });
  },
});

export const getProfileImage = userQuery({
  args: { userId: v.id("users") },
  handler: async (ctx, args) => {
    const user = await ctx.db.get(args.userId);
    if (!user?.profileImageId) return null;
    return await ctx.storage.getUrl(user.profileImageId);
  },
});
```

## Swift: Image Picker View

```swift
import SwiftUI
import PhotosUI
import ConvexMobile

struct ProfileImagePicker: View {
    @StateObject private var viewModel = ImageUploadViewModel()
    @State private var selectedItem: PhotosPickerItem?

    var body: some View {
        VStack(spacing: 16) {
            if let imageUrl = viewModel.currentImageUrl {
                AsyncImage(url: URL(string: imageUrl)) { phase in
                    switch phase {
                    case .empty:
                        ProgressView()
                    case .success(let image):
                        image
                            .resizable()
                            .scaledToFill()
                            .frame(width: 120, height: 120)
                            .clipShape(Circle())
                    case .failure:
                        Image(systemName: "person.circle.fill")
                            .resizable()
                            .frame(width: 120, height: 120)
                            .foregroundStyle(.secondary)
                    @unknown default:
                        EmptyView()
                    }
                }
            } else {
                Image(systemName: "person.circle.fill")
                    .resizable()
                    .frame(width: 120, height: 120)
                    .foregroundStyle(.secondary)
            }

            PhotosPicker(
                selection: $selectedItem,
                matching: .images,
                photoLibrary: .shared()
            ) {
                Label(
                    viewModel.isUploading ? "Uploading..." : "Change Photo",
                    systemImage: "camera"
                )
            }
            .disabled(viewModel.isUploading)

            if let error = viewModel.error {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        }
        .onChange(of: selectedItem) { _, newItem in
            guard let item = newItem else { return }
            Task {
                await viewModel.uploadImage(item: item)
            }
        }
        .task {
            viewModel.subscribeToProfileImage()
        }
    }
}
```

## ViewModel: Upload And Display

```swift
import Combine
import PhotosUI
import ConvexMobile

class ImageUploadViewModel: ObservableObject {
    @Published var currentImageUrl: String?
    @Published var isUploading = false
    @Published var error: String?

    private var cancellables = Set<AnyCancellable>()

    func subscribeToProfileImage() {
        client.subscribe(
            to: "images:getProfileImage",
            with: ["userId": "current"],
            yielding: String?.self
        )
        .receive(on: DispatchQueue.main)
        .sink(
            receiveCompletion: { [weak self] completion in
                if case .failure(let error) = completion {
                    self?.error = error.localizedDescription
                }
            },
            receiveValue: { [weak self] url in
                self?.currentImageUrl = url
            }
        )
        .store(in: &cancellables)
    }

    func uploadImage(item: PhotosPickerItem) async {
        await MainActor.run {
            isUploading = true
            error = nil
        }

        do {
            guard let data = try await item.loadTransferable(type: Data.self) else {
                throw ImageUploadError.loadFailed
            }

            guard let uiImage = UIImage(data: data),
                  let compressed = uiImage.jpegData(compressionQuality: 0.8) else {
                throw ImageUploadError.compressionFailed
            }

            // Step 1: Get upload URL
            let uploadUrl: String = try await client.mutation(
                "images:generateUploadUrl",
                with: [:]
            )

            // Step 2: POST compressed image via URLSession
            var request = URLRequest(url: URL(string: uploadUrl)!)
            request.httpMethod = "POST"
            request.setValue("image/jpeg", forHTTPHeaderField: "Content-Type")
            let (responseData, _) = try await URLSession.shared.upload(for: request, from: compressed)
            let uploadResponse = try JSONDecoder().decode(UploadResponse.self, from: responseData)
            let storageId = uploadResponse.storageId

            // Step 3: Save storageId to user profile
            try await client.mutation(
                "images:saveProfileImage",
                with: ["storageId": storageId]
            )

            await MainActor.run { isUploading = false }
            // currentImageUrl updates automatically via subscription
        } catch {
            await MainActor.run {
                isUploading = false
                self.error = error.localizedDescription
            }
        }
    }
}

struct UploadResponse: Decodable {
    let storageId: String
}

enum ImageUploadError: LocalizedError {
    case loadFailed
    case compressionFailed

    var errorDescription: String? {
        switch self {
        case .loadFailed: return "Failed to load image from photo library"
        case .compressionFailed: return "Failed to compress image"
        }
    }
}
```

## Compression Guidelines

| Quality | Typical Size (12MP) | Use Case |
|---------|---------------------|----------|
| 1.0 | ~5 MB | Original quality archive |
| 0.8 | ~1.5 MB | Profile photos, thumbnails |
| 0.5 | ~500 KB | Chat image attachments |
| 0.3 | ~200 KB | Low-bandwidth previews |

Always compress before uploading. Raw camera photos can be 10-25 MB.

## macOS Differences

On macOS, `UIImage` is not available. Use `NSImage` with a JPEG compression extension:

```swift
#if os(macOS)
import AppKit

extension NSImage {
    func jpegData(compressionQuality: CGFloat) -> Data? {
        guard let tiffData = self.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiffData) else { return nil }
        return bitmap.representation(
            using: .jpeg,
            properties: [.compressionFactor: compressionQuality]
        )
    }
}
#endif
```

## AsyncImage Caching

`AsyncImage` uses `URLCache` internally. Convex storage URLs include a token that changes when the file changes, so cache invalidation happens automatically. No manual cache busting is needed.

## Avoid
- Uploading raw uncompressed camera photos — they can be 10-25 MB each.
- Using `.replaceError(with:)` on the subscription publisher — it emits the fallback then **completes** permanently, killing live updates.
- Skipping the three-step upload flow — there is no single-call upload API.
- Calling component or storage functions directly from the Swift client — always go through your own wrapper mutations and queries.

## Read Next
- [02-file-storage-upload-download-and-document-ids.md](02-file-storage-upload-download-and-document-ids.md)
- [04-streaming-workloads-and-transcription.md](04-streaming-workloads-and-transcription.md)
- [../swiftui/07-loading-error-data-tri-state-pattern.md](../swiftui/07-loading-error-data-tri-state-pattern.md)
