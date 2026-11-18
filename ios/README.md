# iOS app

The Balance iPhone app, written in Swift with SwiftUI.

## Run it

You need a Mac with Xcode 16 or later and Docker Desktop.

1. **Start the backend** (in Terminal, from the repo root). The first two commands are only needed once.

   ```sh
   cd backend
   python3.12 -m venv .venv
   .venv/bin/python -m pip install -e '.[dev]'
   docker compose up -d --wait
   .venv/bin/python -m app.seed
   .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

   Leave this running. `app.seed` resets the demo data ($152 spent of a $350 weekly budget); run it again any time to start over.

2. **Run the app.** Open `ios/Balance.xcodeproj` in Xcode, pick any iPhone Simulator at the top, and press **Run** (⌘R).

3. **Run the tests.** Press **⌘U** in Xcode. The tests don't need the backend.

The app calls the backend at `http://127.0.0.1:8000`, which only works in the Simulator on the same Mac.

## Where things are

| Folder | What's in it |
| --- | --- |
| `Balance/App/` | `BalanceApp.swift`, where the app starts. |
| `Balance/Core/` | `Budget.swift` (the data the backend sends) and `BudgetAPI.swift` (the calls to the backend). |
| `Balance/Features/Home/` | The Home screen. |
| `BalanceTests/` | Unit tests. |
| `BalanceUITests/` | Reserved for interface tests in a later milestone. |

New Swift files added inside these folders are picked up by Xcode automatically.

## Checks

For the Flow 1 prototype, each iOS pull request builds in Xcode, passes the unit tests (⌘U), and describes a manual walkthrough in the Simulator. See the [development process](../doc/DEVELOPMENT_PROCESS.md#application-gates-to-add-with-implementation).
