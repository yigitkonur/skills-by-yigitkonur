# Implement Morph Animations with Unique transition:name Directives

> **Context:** Routing & Pages | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

The browser View Transition API generates smooth geometry morphs between matching elements across pages. The `transition:name` directive associates an element on the current page with a target element on the next page, allowing card thumbnails to seamlessly expand into full-width hero images upon navigation.

## 2. How It Differs From Classic React / Next.js

In React, morph animations typically require external heavy animation libraries like Framer Motion (`layoutId`). In Astro, morph animations compile to native CSS `view-transition-name` properties with zero additional client JavaScript runtime cost.

## 3. Common Mistakes & Anti-Patterns

Reusing the same `transition:name` across multiple elements rendered on the **same page** (e.g. inside a `.map()` list). The View Transitions API strictly requires `view-transition-name` to be unique per page; duplicate names cause the transition to fail or abort.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/blog/index.astro
const posts = await getPosts();
---
<ul>
  {posts.map(post => (
    <li>
      <!-- FATAL ERROR: Duplicate transition:name on the same page! -->
      <img src={post.image} transition:name="post-cover" />
      <a href={`/blog/${post.slug}`}>{post.title}</a>
    </li>
  ))}
</ul>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/blog/index.astro
const posts = await getPosts();
---
<ul>
  {posts.map(post => (
    <li>
      <!-- Dynamic, slug-scoped name guarantees uniqueness on the listing page -->
      <img
        src={post.image}
        alt={post.title}
        transition:name={`hero-${post.slug}`}
      />
      <a href={`/blog/${post.slug}`}>{post.title}</a>
    </li>
  ))}
</ul>
```

```astro
---
// src/pages/blog/[slug].astro
const { slug } = Astro.params;
const post = await getPostBySlug(slug);
---
<article>
  <!-- Matches the exact transition:name from the clicked listing item -->
  <img
    src={post.image}
    alt={post.title}
    transition:name={`hero-${slug}`}
    transition:animate="fade"
  />
  <h1>{post.title}</h1>
</article>
```

## 4. Verification & Audit

Click from the blog index list to the detail page. Observe the image smoothly transform and expand into the hero position without jumping. Check DevTools console for zero `Duplicate view-transition-name` errors.
