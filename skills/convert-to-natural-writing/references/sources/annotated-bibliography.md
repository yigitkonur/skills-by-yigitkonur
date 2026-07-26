# Annotated Bibliography

Use this reference to trace the skill's editorial, multilingual, detector-limitation, accessibility, inclusion, and format-preservation rules to sources. Accessed 2026-07-26 unless noted.

## How to read this bibliography

The sources do different jobs. Editorial guides provide usable practices; research papers bound claims about multilingual evaluation and detectors; technical specifications define syntax. No source is treated as a universal voice guide or an authorship oracle.

## AI-writing sign taxonomy

### Wikipedia: Signs of AI writing

- URL: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- Type: community-maintained descriptive taxonomy
- Contribution: catalogs recurring content, language, style, formatting, citation, and communication patterns observed in Wikipedia editing.
- Crucial limit: the page frames signs as descriptive rather than prescriptive and as potential signs of a problem rather than the problem itself.
- Used here: prompts for contextual diagnosis, production-residue checks, and non-signal warnings.
- Not used for: word bans, punctuation bans, authorship classification, detector optimization, or universal rules across languages.

This source inspired the diagnosis vocabulary, but the skill requires a reader-impact explanation before any edit.

## Reader-centered editorial guidance

### PlainLanguage.gov: Federal plain-language guidelines

- URL: https://www.plainlanguage.gov/guidelines/
- Type: public-sector plain-language guidance archive
- Contribution: write for a specific audience, organize around reader needs, use clear wording, and evaluate whether people can use the content.
- Used here: editorial contract, reader job, clear actor/action, and comprehension focus.
- Limit: plain language is audience-relative; it does not justify stripping necessary expert terminology.

### GOV.UK: Writing for GOV.UK

- URL: https://www.gov.uk/guidance/content-design/writing-for-gov-uk
- Type: government content-design standard
- Contribution: begin with user needs, publish content that helps people know or do something, and keep content accessible and current.
- Used here: purpose-first openings, section jobs, and publication accountability.
- Limit: GOV.UK voice and service conventions are not universal brand rules.

### Microsoft Writing Style Guide

- URL: https://learn.microsoft.com/en-us/style-guide/welcome/
- Type: product-writing style guide
- Contribution: warm and relaxed, crisp and clear, useful, and oriented around the key takeaway.
- Used here: one evidence-backed model for casual-professional voice.
- Limit: Microsoft-specific terminology and brand personality were not imported.

### Google developer documentation: Tone and content

- URL: https://developers.google.com/style/tone
- Type: developer-documentation style guidance
- Contribution: conversational, friendly, respectful writing for a global audience; avoid forced informality, cutesiness, slang, and unnecessary jargon.
- Used here: knowledgeable-friend calibration, global-audience caution, and read-aloud review.
- Limit: developer documentation is only one genre.

### Mailchimp Content Style Guide: Voice and tone

- URL: https://styleguide.mailchimp.com/voice-and-tone/
- Type: public brand content guide
- Contribution: separates a relatively stable voice from tone that adapts to the reader's situation and emotional state.
- Used here: context-sensitive warmth and avoidance of humor when the reader is under stress.
- Limit: Mailchimp's specific personality is not the default voice.

### Purdue OWL: Tone, mood, and audience

- URL: https://owl.purdue.edu/owl/general_writing/writing_style/diction/tone_mood_audience.html
- Type: university writing guidance
- Contribution: audience, purpose, diction, tone, and expected knowledge affect appropriate writing choices.
- Used here: reader expertise and genre calibration.
- Limit: broad educational guidance, not a locale-specific publication standard.

## Accessibility and inclusion

### W3C WAI: Tips for writing

- URL: https://www.w3.org/WAI/tips/writing/
- Type: web accessibility guidance
- Contribution: clear instructions, meaningful headings and links, expanded abbreviations, and digestible sentences and paragraphs help more readers.
- Used here: web clarity, meaningful link-label review, and scannable structure.
- Limit: “short” is not a mechanical sentence-length quota; meaning and audience still govern.

### APA Style: Bias-free language

- URL: https://apastyle.apa.org/style-grammar-guidelines/bias-free-language
- Type: research and professional style guidance
- Contribution: accurate, specific, relevant description; attention to self-identification; avoidance of labels that reduce people to a characteristic.
- Used here: inclusive-language questions, group-comparison checks, and relevance gate.
- Limit: terminology changes by community, locale, domain, and time; subject preference outranks a generic rule.

## Multilingual and internationalization evidence

### W3C Internationalization: Authoring HTML and CSS

- URL: https://www.w3.org/International/techniques/authoring-html
- Type: web internationalization techniques
- Contribution: declare document language, identify language changes, preserve directionality and bidi behavior, and provide context for translators.
- Used here: exact protection of `lang`, `dir`, mixed-language spans, and format-aware locale review.
- Limit: technical internationalization does not by itself establish natural prose.

### Hada et al. (2024): Are Large Language Model-based Evaluators the Solution to Scaling Up Multilingual Evaluation?

- URL: https://aclanthology.org/2024.findings-eacl.103/
- Venue: Findings of EACL 2024
- Contribution: multilingual evaluator behavior was calibrated against 20,000 human judgments, highlighting language-specific reliability differences and the need for native-speaker calibration, particularly beyond high-resource Latin-script settings.
- Used here: explicit confidence labels and fluent-review gates.
- Limit: evaluator findings do not yield a universal ranking of writing quality or a guarantee for every language-task pair.

### UNESCO: Multilingualism and linguistic diversity

- URL: https://www.unesco.org/en/multilingualism-linguistic-diversity
- Type: intergovernmental overview
- Contribution: language carries sociocultural context and multilingual access supports inclusion and participation.
- Used here: high-level rationale for composing the locale rather than treating language as interchangeable surface text.
- Limit: not a sentence-level editing guide.

## Detector limitations and linguistic bias

### Liang et al. (2023): GPT detectors are biased against non-native English writers

- URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC10028438/
- Journal: Patterns 4(7), 2023
- Contribution: across seven detectors, 91 TOEFL essays and 88 US eighth-grade essays were evaluated; the reported average false-positive rate on TOEFL essays was 61.3%, and vocabulary-oriented changes affected classifications.
- Used here: strong prohibition on detector-facing optimization and caution about linguistic bias.
- Limit: the result applies to the tested detectors, thresholds, datasets, and period. It is not a current false-positive rate for every tool.

### Weber-Wulff et al. (2023): Testing of detection tools for AI-generated text

- URL: https://edintegrity.biomedcentral.com/articles/10.1007/s40979-023-00146-z
- Journal: International Journal for Educational Integrity 19, 2023
- Contribution: evaluated multiple detection tools and reported serious accuracy and obfuscation limitations.
- Used here: detector scores cannot certify authorship or serve as sole decision evidence.
- Limit: tools evolve; the general integrity lesson is stronger than any per-tool score from the study.

### Turnitin: AI-writing detection guidance

- URL: https://guides.turnitin.com/hc/en-us/articles/28457596598925-AI-writing-detection-model
- Type: vendor documentation
- Contribution: vendor-facing context for false positives, score interpretation, and human review.
- Used here: only to show that even a detector vendor frames output within contextual review.
- Limit: vendor accuracy claims are not independent validation; the page returned an automated-access restriction during the 2026-07-26 verification pass, so no time-sensitive numeric claim from it is embedded in this skill.

### Vanderbilt University: institutional detector guidance

- Type: institutional operational guidance published in 2023
- Contribution: documented the decision to disable Turnitin's AI detector amid reliability, transparency, and false-positive concerns.
- Used here: an operational example of why detector scores are not publication objectives.
- Limit: the institution's original URL was not stable in the 2026-07-26 verification pass; this source is retained as historical context, not as the basis for a standalone rule.

## Format specifications

### CommonMark Specification 0.31.2

- URL: https://spec.commonmark.org/0.31.2/
- Published: 2024-01-28
- Type: Markdown syntax specification
- Contribution: precise rules for links, code spans, fenced code, raw HTML, blocks, and whitespace; fenced code contents are literal.
- Used here: exact inventory of code and destinations plus parser-aware preservation.
- Limit: consuming projects may use a CommonMark extension or another Markdown dialect.

### MDX: What is MDX?

- URL: https://mdxjs.com/docs/what-is-mdx/
- Type: official MDX documentation
- Contribution: MDX combines Markdown with JSX, expressions, and ESM; prose and executable structure share a file.
- Used here: protection of component syntax, props, expressions, imports, and delimiter-sensitive regions.
- Limit: project plugins and MDX versions may add further syntax; the repository compiler is authoritative.

### WHATWG HTML Living Standard

- URL: https://html.spec.whatwg.org/multipage/
- Type: living web-platform specification
- Verified page update during research: 2026-07-20
- Contribution: HTML parsing, element/attribute syntax, DOM meaning, and language semantics depend on structure, not visual appearance alone.
- Used here: tag, attribute, nesting, language, and DOM-preservation rules.
- Limit: the skill's helper is not an HTML conformance checker; use validators and actual browsers.

## Source-selection rules

- Use current primary specifications for syntax and parser behavior.
- Use official style guides as examples of a voice system, not universal law.
- Use peer-reviewed research to bound detector and multilingual claims.
- Keep Wikipedia's taxonomy contextual and descriptive.
- Treat vendor claims as vendor claims.
- Mark unstable or inaccessible historical sources instead of pretending live verification.
- Re-check dates, URLs, and current guidance when revising the skill.

## Completion check

- Every source has a defined contribution and limit.
- No single guide becomes a universal voice standard.
- Detector studies are scoped to their datasets and dates.
- Technical rules point to specifications and still require the consuming parser.
- Unstable sources are disclosed and do not carry load-bearing claims.
