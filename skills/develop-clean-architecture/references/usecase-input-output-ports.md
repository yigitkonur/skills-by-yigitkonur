---
title: Define Input and Output Ports for Use Cases
impact: HIGH
impactDescription: decouples use cases from delivery mechanism
tags: usecase, ports, input, output, boundaries
---

## Define Input and Output Ports for Use Cases

Use cases should define their own input (request) and output (response) data structures. These ports isolate the use case from the delivery mechanism (HTTP, CLI, queue).
Adapters still own parsing and request-shape validation; the use case should accept an already-parsed command and return a delivery-agnostic response.

**Incorrect (use case coupled to HTTP):**

```csharp
public class RegisterUserUseCase
{
    public IActionResult Execute(HttpRequest request)  // Coupled to ASP.NET
    {
        var email = request.Form["email"];
        var password = request.Form["password"];

        if (string.IsNullOrEmpty(email))
            return new BadRequestResult();  // HTTP-specific response

        var user = new User(email, password);
        _repository.Save(user);

        return new OkObjectResult(new { id = user.Id });  // JSON response
    }
}
```

**Correct (use case with defined ports):**

```csharp
// application/ports/input/RegisterUserCommand.cs
public record RegisterUserCommand(
    EmailAddress Email,
    PlainTextPassword Password,
    PersonName Name
);

// application/ports/output/RegisterUserResult.cs
public record RegisterUserResult(
    string UserId,
    string Email,
    DateTime CreatedAt
);

// application/usecases/RegisterUserUseCase.cs
public class RegisterUserUseCase
{
    private readonly IUserRepository _repository;
    private readonly IPasswordHasher _hasher;

    public RegisterUserResult Execute(RegisterUserCommand command)
    {
        var hashedPassword = _hasher.Hash(command.Password);
        var user = User.Register(command.Email, hashedPassword, command.Name);
        _repository.Save(user);

        return new RegisterUserResult(
            user.Id.Value,
            user.Email.Value,
            user.CreatedAt
        );
    }
}

// interface_adapters/controllers/UserController.cs
[ApiController]
public class UserController : ControllerBase
{
    private readonly RegisterUserUseCase _useCase;
    private readonly IRegisterUserRequestValidator _validator;

    public UserController(
        RegisterUserUseCase useCase,
        IRegisterUserRequestValidator validator)
    {
        _useCase = useCase;
        _validator = validator;
    }

    [HttpPost]
    public IActionResult Register([FromBody] RegisterRequest request)
    {
        var validation = _validator.Validate(request);
        if (!validation.IsValid)
            return BadRequest(validation.Errors);

        var command = new RegisterUserCommand(
            EmailAddress.Parse(request.Email),
            PlainTextPassword.Parse(request.Password),
            PersonName.Parse(request.Name)
        );

        var result = _useCase.Execute(command);

        return Ok(new { userId = result.UserId });
    }
}
```

**Benefits:**
- Same use case callable from HTTP, CLI, message queue, tests
- Request/response format changes don't affect use case
- Use case testable without HTTP infrastructure

Reference: [Clean Architecture - Input/Output Ports](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
