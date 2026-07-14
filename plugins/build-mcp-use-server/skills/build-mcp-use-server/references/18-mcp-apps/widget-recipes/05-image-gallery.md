# Recipe 05 — Image Gallery With Lightbox

**What it demonstrates:** image rendering with CSP `resourceDomains`, click-to-open lightbox, theme-aware overlay, follow-up message about a selected image.

Synthesized from the source product-carousel pattern; adapted for image-first content where the image origin (CDN) is the load-bearing CSP entry.

## File layout

```
resources/image-gallery/
└── widget.tsx
src/tools/images.ts
```

## Server tool — `src/tools/images.ts`

```typescript
import { widget } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerImageTools(server: MCPServer) {
  server.tool(
    {
      name: "search-images",
      description: "Search a stock-image library and render the results as a gallery",
      schema: z.object({
        query: z.string().describe("Search keyword (e.g. 'mountain sunrise')"),
        limit: z.number().int().min(1).max(24).default(12).describe("How many images to fetch"),
      }),
      widget: {
        name: "image-gallery",
        invoking: "Searching images...",
        invoked: "Gallery ready",
      },
    },
    async ({ query, limit }) => {
      // Replace with a real image-search API; the URL origin must match resourceDomains in widgetMetadata.
      const images = Array.from({ length: limit }, (_, i) => ({
        id: `img-${i + 1}`,
        url: `https://picsum.photos/seed/${encodeURIComponent(query)}-${i}/800/600`,
        thumb: `https://picsum.photos/seed/${encodeURIComponent(query)}-${i}/240/180`,
        alt: `${query} #${i + 1}`,
        photographer: `Photographer ${(i % 5) + 1}`,
      }));

      return widget({
        props: { query, images },
        message: `Found ${images.length} images for "${query}"`,
      });
    }
  );
}
```

## Widget — `resources/image-gallery/widget.tsx`

```tsx
import { useState } from "react";
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Searchable image gallery with click-to-zoom lightbox",
  props: z.object({
    query: z.string(),
    images: z.array(z.object({
      id: z.string(),
      url: z.string(),
      thumb: z.string(),
      alt: z.string(),
      photographer: z.string(),
    })),
  }),
  metadata: {
    csp: {
      resourceDomains: ["https://picsum.photos"],
    },
    prefersBorder: true,
  },
};

interface ImageItem {
  id: string;
  url: string;
  thumb: string;
  alt: string;
  photographer: string;
}

interface GalleryProps {
  query: string;
  images: ImageItem[];
}

function GalleryContent() {
  const { props, isPending, theme, sendFollowUpMessage } = useWidget<GalleryProps>();
  const [openImage, setOpenImage] = useState<ImageItem | null>(null);
  const isDark = theme === "dark";

  if (isPending) {
    return (
      <div className="grid grid-cols-3 gap-2 p-4 animate-pulse">
        {[...Array(9)].map((_, i) => (
          <div
            key={i}
            className={`aspect-square rounded ${isDark ? "bg-gray-800" : "bg-gray-200"}`}
          />
        ))}
      </div>
    );
  }

  return (
    <div className={`p-4 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <h2 className="text-lg font-bold mb-3">
        Images for "{props.query}"
        <span className={`ml-2 text-sm font-normal ${isDark ? "text-gray-400" : "text-gray-500"}`}>
          ({props.images.length})
        </span>
      </h2>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {props.images.map((img) => (
          <button
            key={img.id}
            onClick={() => setOpenImage(img)}
            className="aspect-square overflow-hidden rounded group focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <img
              src={img.thumb}
              alt={img.alt}
              loading="lazy"
              className="w-full h-full object-cover transition-transform group-hover:scale-105"
            />
          </button>
        ))}
      </div>

      {openImage && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
          onClick={() => setOpenImage(null)}
        >
          <div
            className={`max-w-3xl max-h-[90vh] rounded-lg overflow-hidden ${isDark ? "bg-gray-900" : "bg-white"}`}
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={openImage.url}
              alt={openImage.alt}
              className="w-full h-auto max-h-[70vh] object-contain"
            />
            <div className="p-4 flex justify-between items-center gap-4">
              <div>
                <p className="font-medium">{openImage.alt}</p>
                <p className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>
                  by {openImage.photographer}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() =>
                    sendFollowUpMessage(
                      `Tell me more about the kind of imagery in "${openImage.alt}" — composition, mood, likely use cases.`
                    )
                  }
                  className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  Ask AI →
                </button>
                <button
                  onClick={() => setOpenImage(null)}
                  className={`px-3 py-1.5 text-sm rounded ${isDark ? "bg-gray-700" : "bg-gray-200"}`}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <GalleryContent />
    </McpUseProvider>
  );
}
```

## What to copy when adapting

| Concern | Where it lives |
|---|---|
| Image origin in CSP | `widgetMetadata.metadata.csp.resourceDomains: ["https://picsum.photos"]` — every CDN you load from must be listed |
| Two-resolution loading | Server returns `thumb` (small) + `url` (full); grid uses `thumb`, lightbox uses `url` |
| Lightbox open/close | Local `useState<ImageItem | null>` — never use `setState` for ephemeral UI |
| Theme-aware overlay | `bg-black/80` is universal; the inner card uses `theme === "dark"` |
| Follow-up about a selection | `sendFollowUpMessage` carries the selected item's caption to the model |
| Lazy loading | `loading="lazy"` on grid thumbnails; the lightbox image loads on demand |
