# Multilingual Before-and-After Examples

Use this reference when a concrete model is more useful than another rule. Each example shows protected content, the editorial problem, and a bounded rewrite.

## How to use these examples

Copy the method, not the wording. Every real rewrite needs its own reader, locale, evidence, and protected-content ledger. The examples do not authorize invented details.

## Example 1: English technical marketing

### Source

> In today's rapidly evolving digital landscape, our robust platform empowers modern organizations to seamlessly unlock actionable insights. Moreover, it delivers a transformative end-to-end experience that drives efficiency and growth. Learn more in [our methodology](https://example.com/method).

### Ledger

```text
Exact: https://example.com/method
Value: platform provides insights; methodology link
Force: no metrics or causal proof supplied
Document: technical marketing; retain CTA
```

### Diagnosis

- The opening could introduce almost any software product.
- Four evaluations—“robust,” “seamlessly,” “transformative,” and “drives”—have no supplied mechanism or evidence.
- “Moreover” adds no logical relationship.

### Rewrite without invented specificity

> The platform brings your reporting data into one place, so teams can review the same information before deciding what to do next. See [our methodology](https://example.com/method).

This rewrite is valid only if “brings reporting data into one place” is supplied elsewhere. If it is not, block that mechanism and request product evidence instead of guessing.

## Example 2: English evidence and uncertainty

### Source

> Our 2025 review demonstrates that 12.5% of sampled pages require remediation, proving that the new process is essential.

### Ledger

```text
Value: 2025; 12.5%; sampled pages
Force: source may support observation, not “require,” proof, causality, or essentiality
```

### Safe rewrite

> In our 2025 review, 12.5% of the sampled pages needed another check. The result helps identify where the process may need more support.

If the source actually uses “require remediation,” preserve it. The rewrite must follow source authority, not automatically weaken or strengthen claims.

## Example 3: Turkish professional copy

### Source

> Günümüzün hızla değişen dijital ekosisteminde, markaların rekabet avantajı elde etmek için yenilikçi ve bütünsel çözümlerden yararlanması kritik öneme sahiptir. Bu kapsamda platformumuz, verimliliği artırarak sürdürülebilir büyümenin önünü açar.

### Ledger

```text
Locale: tr-TR, professional conversational
Value: a platform is offered; no supplied metric or causal evidence
Force: “sürdürülebilir büyümenin önünü açar” is unsupported
```

### Rewrite when supplied product detail supports shared review

> Platform, raporları ve ekip yorumlarını aynı çalışma alanında toplar. Böylece herkes karar vermeden önce aynı güncel veriyi inceler.

### Why it works

- It begins with the product action rather than generic market context.
- The consequence follows from the supplied workflow detail.
- It does not insert informal slang, a fictional customer, or an unsourced performance metric.

## Example 4: Turkish high-stakes limitation

### Source

> Bu yöntem hataları ortadan kaldırır ve tüm kullanıcılar için güvenli sonuçlar sağlar.

### Supplied evidence

> Testlerde bazı giriş hataları azaldı; çalışma 40 oturumla sınırlıydı.

### Rewrite

> 40 oturumluk testte bazı giriş hataları azaldı. Bu sonuç, yöntemin tüm hataları ortadan kaldırdığını veya her kullanıcı için aynı sonucu vereceğini göstermiyor.

The rewrite restores sample scope and rejects a universal safety claim. A qualified domain reviewer is still required if “safe” has legal, medical, or security meaning.

## Example 5: Spanish product instruction

### Source

> Con el objetivo de poder proceder a la finalización exitosa del proceso, será necesario que los usuarios realicen primeramente la verificación de la dirección de correo electrónico correspondiente.

### Contract

```text
Locale: es-MX
Voice: direct product guidance, informal singular used across interface
Value: email verification occurs before completion
```

### Rewrite

> Para completar el proceso, verifica primero tu correo electrónico.

For a formal plural interface, the pronoun and verb form must change. The locale contract controls the choice.

## Example 6: German expert documentation

### Source

> Es ist wichtig zu beachten, dass die Transaktion unter Umständen wiederholt werden könnte, falls es möglicherweise zu einem Timeout kommt.

### Rewrite

> Bei einem Timeout kann das System die Transaktion wiederholen.

### Protection check

The modal `kann` retains possibility. Do not change it to `wiederholt` or `wird wiederholen`, which would imply certainty. A domain reviewer must confirm whether the system or user initiates the retry.

## Example 7: Markdown links and code

### Source

```md
To begin your exciting journey, run `pnpm verify` and explore [the complete guide](https://example.com/docs?lang=en).

```bash
pnpm verify --filter "site"
```
```

### Ledger

```text
Exact: `pnpm verify`; URL destination; entire fenced block
Editable: surrounding prose and visible link label
```

### Rewrite

```md
Run `pnpm verify`, then check [the guide](https://example.com/docs?lang=en) if the command reports an error.

```bash
pnpm verify --filter "site"
```
```

The code and destination remain exact. The rewrite gives the link a clearer conditional job.

## Example 8: MDX component copy

### Source

```mdx
<Callout tone="warning" title="Important Note">
  It is important to note that your API key may possibly expire.
</Callout>
```

### Ledger

```text
Exact: Callout; tone; warning
Editable: title and child prose
Force: API key may expire
```

### Rewrite

```mdx
<Callout tone="warning" title="Check your API key">
  Your API key may have expired.
</Callout>
```

Run the project's MDX compiler because regex inventory cannot validate JSX structure.

## Example 9: HTML with language change

### Source

```html
<p lang="en">Use the <span lang="tr">Ayarlar</span> menu to continue.</p>
```

### Rewrite

```html
<p lang="en">Continue from the <span lang="tr">Ayarlar</span> menu.</p>
```

`lang` values, nesting, and the untranslated UI label remain exact. Do not remove the inner language marker as visual clutter.

## Example 10: Refusing invented personality inside the deliverable

### Request

> Add a funny story about how I learned this the hard way so it sounds human.

### Safe handling

> I can make the passage warmer, but I won't invent a personal experience. If you share what happened, I can shape it into the piece.

Then rewrite the supported content without the anecdote. Do not stop the whole editorial task unless the anecdote is essential to the requested genre.

## Example 11: Diagnosis, not authorship scoring

### Source

> Moreover, the system is robust. Furthermore, it is seamless. In conclusion, this innovative solution is transformative.

### Diagnosis output

```text
Excerpt: the full paragraph
Issue: Three transitions imply a logical progression, but each sentence only repeats unsupported praise.
Reader impact: The reader gets no mechanism, evidence, or decision-relevant difference.
Evidence level: Contextual editorial signal; not an authorship indicator.
Smallest useful change: Replace the paragraph with the supported product action, evidence, and limitation—or remove it.
```

## Completion check

- Each example begins from supplied evidence and a bounded contract.
- Rewrites preserve exact tokens, factual values, and claim force.
- Non-English examples are recomposed for locale rather than translated from a fixed English template.
- Structured examples preserve code, destinations, tags, attributes, and language metadata.
- No example uses detector scores, fabricated biography, fake errors, or invented metrics as a quality strategy.
