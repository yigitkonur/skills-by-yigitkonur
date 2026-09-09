# Architecture: Go & Gin Sentry Integration

How to configure Sentry in Go applications using `sentry-go` with Gin middleware and panic recovery.

## Installation

```bash
go get github.com/getsentry/sentry-go
go get github.com/getsentry/sentry-go/gin
```

## Gin Middleware Setup (`main.go`)

```go
package main

import (
	"log"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/getsentry/sentry-go"
	sentrygin "github.com/getsentry/sentry-go/gin"
)

func main() {
	err := sentry.Init(sentry.ClientOptions{
		Dsn:              os.Getenv("SENTRY_DSN"),
		Environment:      os.Getenv("APP_ENV"),
		EnableTracing:    true,
		TracesSampleRate: 1.0,
		BeforeSend: func(event *sentry.Event, hint *sentry.EventHint) *sentry.Event {
			if event.Request != nil && event.Request.Headers != nil {
				delete(event.Request.Headers, "Authorization")
				delete(event.Request.Headers, "X-Api-Key")
			}
			return event
		},
	})
	if err != nil {
		log.Fatalf("sentry.Init: %s", err)
	}
	defer sentry.Flush(2 * time.Second)

	router := gin.Default()
	router.Use(sentrygin.New(sentrygin.Options{
		Repanic: true,
	}))

	router.GET("/api/ping", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "pong"})
	})

	router.Run(":8080")
}
```
