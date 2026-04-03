# Channel and Provider Setup

OpenClaw plugins can register four types of non-tool extension points: channels, model providers, speech providers, and image generators. Each follows a similar pattern — declare in the manifest, implement the interface, export from the plugin.

Verify the actual Plugin SDK import path in the target runtime before copying any example below. The `@openclaw/sdk` imports shown here are illustrative; some OpenClaw deployments expose these interfaces from a monorepo package or private runtime path instead of a public npm package.

## Channels

Channels are communication interfaces that connect OpenClaw to external messaging platforms.

### When to build a channel

- You need OpenClaw to receive messages from a platform (Telegram, Discord, Slack, custom webhook)
- You need OpenClaw to send messages back through that platform
- You want bidirectional real-time communication with users

### Channel implementation pattern

```typescript
// src/channels/telegram.ts
import { Channel, IncomingMessage, OutgoingMessage } from '@openclaw/sdk';

export class TelegramChannel implements Channel {
  name = 'telegram';

  async initialize(config: Record<string, string>): Promise<void> {
    // Set up webhook or polling with config.TELEGRAM_BOT_TOKEN
    // This runs once when the plugin loads
  }

  async sendMessage(message: OutgoingMessage): Promise<void> {
    // Send a message through the Telegram Bot API
    // Handle formatting, media attachments, etc.
  }

  onMessage(handler: (message: IncomingMessage) => Promise<void>): void {
    // Register the callback that OpenClaw calls when a message arrives
    // Route incoming Telegram messages to this handler
  }

  async shutdown(): Promise<void> {
    // Clean up: close webhooks, stop polling
  }
}
```

### Manifest declaration for channels

```json
{
  "channels": ["telegram"],
  "metadata": {
    "openclaw": {
      "requires": {
        "config": ["TELEGRAM_BOT_TOKEN"]
      }
    }
  }
}
```

### Channel design rules

- Always gate on required config keys (API tokens, webhook URLs)
- Implement `shutdown()` to clean up connections
- Handle message formatting differences between platforms
- Normalize incoming messages to OpenClaw's `IncomingMessage` format
- Support attachments (images, files) if the platform does
- Log connection events for debugging

## Model providers

Model providers connect OpenClaw to LLM backends.

### When to build a model provider

- You have a custom or self-hosted LLM endpoint
- You need to integrate a model API not already supported
- You want to add a proxy layer (caching, logging, routing)

### Model provider implementation pattern

```typescript
// src/providers/custom-model.ts
import { ModelProvider, ChatRequest, ChatResponse } from '@openclaw/sdk';

export class CustomModelProvider implements ModelProvider {
  name = 'custom-model';

  async initialize(config: Record<string, string>): Promise<void> {
    // Validate API endpoint, test connectivity
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    // Send the chat request to your model endpoint
    // Transform OpenClaw's request format to your API's format
    // Transform the response back to OpenClaw's format
    return {
      message: {
        role: 'assistant',
        content: responseText,
      },
      usage: {
        promptTokens: usage.prompt,
        completionTokens: usage.completion,
      },
      // Include tool calls if the model supports them
      toolCalls: parsedToolCalls,
    };
  }

  async streamChat(request: ChatRequest): AsyncGenerator<ChatResponseChunk> {
    // Streaming variant — yield chunks as they arrive
  }

  getModels(): string[] {
    // Return list of model IDs this provider supports
    return ['custom-model-v1', 'custom-model-v2'];
  }

  async shutdown(): Promise<void> {
    // Clean up connections
  }
}
```

### Manifest declaration for model providers

```json
{
  "modelProviders": ["custom-model"],
  "metadata": {
    "openclaw": {
      "requires": {
        "config": ["CUSTOM_MODEL_API_KEY", "CUSTOM_MODEL_ENDPOINT"]
      }
    }
  }
}
```

### Model provider design rules

- Always return token usage counts when available
- Support both streaming and non-streaming if the underlying API does
- Transform tool calls bidirectionally (OpenClaw format to/from provider format)
- Handle rate limits with backoff and clear error messages
- Validate that the model ID exists in `getModels()` before making API calls
- Never log or store conversation content — only metadata

## Speech providers

Speech providers add text-to-speech (TTS) and/or speech-to-text (STT) capabilities.

### Implementation pattern

```typescript
// src/providers/my-tts.ts
import { SpeechProvider, TTSRequest, STTRequest } from '@openclaw/sdk';

export class MyTTSProvider implements SpeechProvider {
  name = 'my-tts';

  capabilities = {
    tts: true,
    stt: false,
  };

  async textToSpeech(request: TTSRequest): Promise<Buffer> {
    // Convert text to audio buffer
    // Respect request.voice, request.speed, request.format
  }

  async speechToText(request: STTRequest): Promise<string> {
    throw new Error('STT not supported by this provider');
  }
}
```

### Speech provider design rules

- Declare capabilities honestly — set `tts` / `stt` to false if not supported
- Support common audio formats (mp3, wav, ogg)
- Handle long text by chunking if the underlying API has length limits
- Cache voice model initialization if it's expensive

## Image generators

Image generators create images from text prompts.

### Implementation pattern

```typescript
// src/providers/my-image-gen.ts
import { ImageGenerator, ImageRequest, ImageResponse } from '@openclaw/sdk';

export class MyImageGen implements ImageGenerator {
  name = 'my-image-gen';

  async generate(request: ImageRequest): Promise<ImageResponse> {
    // Generate image from request.prompt
    // Respect request.size, request.style, etc.
    return {
      url: resultUrl,          // or base64
      revisedPrompt: revised,  // if the provider modifies the prompt
    };
  }
}
```

### Image generator design rules

- Support at least one common size (1024x1024)
- Return either a URL or base64 data, not both
- Include the revised prompt if the provider modifies it (safety filters, prompt enhancement)
- Handle content policy rejections with clear error messages

## Exporting from the plugin

All extension points are exported from the plugin's main entry:

```typescript
// src/index.ts
import { Plugin } from '@openclaw/sdk';
import { TelegramChannel } from './channels/telegram';
import { CustomModelProvider } from './providers/custom-model';
import { searchTool } from './tools/search';

export default class MyPlugin extends Plugin {
  tools = [searchTool];
  channels = [new TelegramChannel()];
  modelProviders = [new CustomModelProvider()];
  // speechProviders = [];
  // imageGenerators = [];
}
```

## Testing extension points

| Extension type | How to test |
|---|---|
| Channel | Mock the platform API, verify message round-trip (incoming -> handler -> outgoing) |
| Model provider | Send a known prompt, verify response format and tool call parsing |
| Speech provider | Convert known text, verify audio buffer is non-empty and correct format |
| Image generator | Generate with known prompt, verify URL or base64 response |

For all types:

- Test `initialize()` with missing config (should throw clearly)
- Test `shutdown()` (should not throw, should clean up)
- Test with malformed input (should return error, not crash)
