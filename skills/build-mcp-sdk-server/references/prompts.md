# Prompts Reference

Prompts are reusable templates that help humans (or client UIs) talk to models in a consistent way. They are declared on the server and listed through MCP.

## Basic Prompt

```typescript
import { z } from 'zod/v4';

server.registerPrompt(
  'review-code',
  {
    title: 'Code Review',
    description: 'Review code for best practices and potential issues',
    argsSchema: z.object({
      code: z.string().describe('Code to review'),
      language: z.string().default('typescript').describe('Programming language'),
    }),
  },
  ({ code, language }) => ({
    messages: [{
      role: 'user' as const,
      content: {
        type: 'text' as const,
        text: `Review this ${language} code for best practices, security issues, and improvements:\n\n\`\`\`${language}\n${code}\n\`\`\``,
      },
    }],
  })
);
```

## Prompt with Completions

Enable autocompletion for prompt arguments:

```typescript
import { completable } from '@modelcontextprotocol/server';

server.registerPrompt(
  'explain-file',
  {
    title: 'Explain File',
    description: 'Explain the purpose and structure of a source file',
    argsSchema: z.object({
      filePath: completable(
        z.string().describe('Path to the file'),
        async (value) => {
          const files = await glob(`**/*${value}*`);
          return files.slice(0, 10);
        }
      ),
    }),
  },
  async ({ filePath }) => {
    const content = await readFile(filePath, 'utf-8');
    return {
      messages: [{
        role: 'user' as const,
        content: {
          type: 'text' as const,
          text: `Explain this file:\n\nPath: ${filePath}\n\n\`\`\`\n${content}\n\`\`\``,
        },
      }],
    };
  }
);
```

## Multi-Message Prompt

Prompts can return multiple messages with different roles:

```typescript
server.registerPrompt(
  'debug-error',
  {
    title: 'Debug Error',
    description: 'Help debug an error with context',
    argsSchema: z.object({
      error: z.string().describe('The error message'),
      stackTrace: z.string().optional().describe('Stack trace if available'),
      context: z.string().optional().describe('Additional context'),
    }),
  },
  ({ error, stackTrace, context }) => ({
    messages: [
      {
        role: 'user' as const,
        content: {
          type: 'text' as const,
          text: [
            `I'm encountering this error: ${error}`,
            stackTrace ? `\nStack trace:\n\`\`\`\n${stackTrace}\n\`\`\`` : '',
            context ? `\nContext: ${context}` : '',
            '\nPlease help me understand what caused this and how to fix it.',
          ].filter(Boolean).join('\n'),
        },
      },
    ],
  })
);
```

## Dynamic Management

Prompts can be updated or removed at runtime:

```typescript
const prompt = server.registerPrompt('my-prompt', config, callback);

prompt.update({
  description: 'Updated description',
  argsSchema: newSchema,
  callback: newCallback,
});

prompt.remove();
```

## Best Practices

1. Write clear `description` fields — they help clients present prompts to users
2. Use `.describe()` on every argument for better UX
3. Provide sensible `.default()` values for optional arguments
4. Use `completable()` for arguments that benefit from autocompletion
5. Keep prompt templates focused on a single task
6. Use multi-message prompts when system context or conversation setup is needed
