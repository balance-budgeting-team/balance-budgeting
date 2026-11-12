# iOS application

Reserved for Balance's native iOS application and test targets. No Xcode project, shared scheme, executable app, or tests exist yet.

- `Balance/App/`: entry point and app setup.
- `Balance/Features/`: feature screens and view models.
- `Balance/Core/`: shared models, networking, and reusable interface components.
- `BalanceTests/`: unit tests.
- `BalanceUITests/`: interface, accessibility, and performance tests.

Add the real project, shared scheme, supported Xcode version, simulator destination, build command, and test command with the first implementation. Application changes require an Xcode build and relevant XCTest/UI checks. User-facing changes also need manual workflows and accessibility checks when affected. See the [development process](../doc/DEVELOPMENT_PROCESS.md#application-gates-to-add-with-implementation).
