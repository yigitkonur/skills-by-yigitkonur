# Complete CRUD Routes with TypeBox Schemas

## Overview

A full Create-Read-Update-Delete pattern using TypeBox for validation and type inference,
with consistent error handling and response schemas.

## Shared Schemas

```typescript
// src/schemas/product.ts
import { Type, type Static } from '@sinclair/typebox'

export const ProductSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  description: Type.String(),
  price: Type.Integer({ description: 'Price in cents' }),
  category: Type.String(),
  inStock: Type.Boolean(),
  createdAt: Type.String({ format: 'date-time' }),
  updatedAt: Type.String({ format: 'date-time' })
}, { $id: 'Product' })

export const CreateProductBody = Type.Object({
  name: Type.String({ minLength: 1, maxLength: 200 }),
  description: Type.String({ maxLength: 2000 }),
  price: Type.Integer({ minimum: 0 }),
  category: Type.String({ minLength: 1 }),
  inStock: Type.Boolean({ default: true })
})

export const UpdateProductBody = Type.Partial(
  Type.Object({
    name: Type.String({ minLength: 1, maxLength: 200 }),
    description: Type.String({ maxLength: 2000 }),
    price: Type.Integer({ minimum: 0 }),
    category: Type.String({ minLength: 1 }),
    inStock: Type.Boolean()
  })
)

export const ListProductsQuery = Type.Object({
  page: Type.Integer({ minimum: 1, default: 1 }),
  limit: Type.Integer({ minimum: 1, maximum: 100, default: 20 }),
  category: Type.Optional(Type.String()),
  search: Type.Optional(Type.String()),
  sort: Type.Optional(Type.Union([
    Type.Literal('name'),
    Type.Literal('price'),
    Type.Literal('createdAt')
  ])),
  order: Type.Optional(Type.Union([Type.Literal('asc'), Type.Literal('desc')]))
})

export const IdParams = Type.Object({
  id: Type.String({ format: 'uuid' })
})

export const ErrorResponse = Type.Object({
  statusCode: Type.Integer(),
  error: Type.String(),
  message: Type.String()
})

export const PaginatedProducts = Type.Object({
  data: Type.Array(ProductSchema),
  pagination: Type.Object({
    page: Type.Integer(),
    limit: Type.Integer(),
    total: Type.Integer(),
    totalPages: Type.Integer()
  })
})

export type Product = Static<typeof ProductSchema>
export type CreateProductInput = Static<typeof CreateProductBody>
export type UpdateProductInput = Static<typeof UpdateProductBody>
```

## CRUD Routes

```typescript
// src/routes/products.ts
import { FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox'
import { Type } from '@sinclair/typebox'
import {
  ProductSchema, CreateProductBody, UpdateProductBody,
  ListProductsQuery, IdParams, ErrorResponse, PaginatedProducts
} from '../schemas/product.js'

const productRoutes: FastifyPluginAsyncTypebox = async (app) => {

  // LIST
  app.get('/', {
    schema: {
      tags: ['Products'],
      summary: 'List products with pagination and filters',
      querystring: ListProductsQuery,
      response: { 200: PaginatedProducts }
    }
  }, async (request) => {
    const { page, limit, category, search, sort, order } = request.query
    const { data, total } = await app.productRepo.list({
      page, limit, category, search, sort, order
    })
    return {
      data,
      pagination: {
        page, limit, total,
        totalPages: Math.ceil(total / limit)
      }
    }
  })

  // GET BY ID
  app.get('/:id', {
    schema: {
      tags: ['Products'],
      summary: 'Get a product by ID',
      params: IdParams,
      response: {
        200: ProductSchema,
        404: ErrorResponse
      }
    }
  }, async (request, reply) => {
    const product = await app.productRepo.findById(request.params.id)
    if (!product) {
      reply.status(404)
      return { statusCode: 404, error: 'Not Found', message: 'Product not found' }
    }
    return product
  })

  // CREATE
  app.post('/', {
    schema: {
      tags: ['Products'],
      summary: 'Create a new product',
      body: CreateProductBody,
      response: {
        201: ProductSchema,
        409: ErrorResponse
      }
    }
  }, async (request, reply) => {
    const product = await app.productRepo.create(request.body)
    reply.status(201)
    return product
  })

  // UPDATE (PATCH)
  app.patch('/:id', {
    schema: {
      tags: ['Products'],
      summary: 'Update a product',
      params: IdParams,
      body: UpdateProductBody,
      response: {
        200: ProductSchema,
        404: ErrorResponse
      }
    }
  }, async (request, reply) => {
    const product = await app.productRepo.update(request.params.id, request.body)
    if (!product) {
      reply.status(404)
      return { statusCode: 404, error: 'Not Found', message: 'Product not found' }
    }
    return product
  })

  // DELETE
  app.delete('/:id', {
    schema: {
      tags: ['Products'],
      summary: 'Delete a product',
      params: IdParams,
      response: {
        204: Type.Null(),
        404: ErrorResponse
      }
    }
  }, async (request, reply) => {
    const deleted = await app.productRepo.delete(request.params.id)
    if (!deleted) {
      reply.status(404)
      return { statusCode: 404, error: 'Not Found', message: 'Product not found' }
    }
    reply.status(204)
  })
}

export default productRoutes
```

## Registration

```typescript
// src/app.ts
app.register(productRoutes, { prefix: '/api/v1/products' })
```

## Key Points

- Use `Type.Partial()` for update schemas (all fields optional)
- Return 201 for successful creation, 204 for successful deletion
- Include pagination metadata in list responses
- Define error response schemas for each possible error status
- Use consistent error format across all endpoints
- Use `$id` on shared schemas to enable `$ref` in OpenAPI output
