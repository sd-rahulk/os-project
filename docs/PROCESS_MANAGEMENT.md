# Remote process management

The process table is fetched from the selected agent on demand. Each row includes the process creation time even though the UI primarily displays the PID. That timestamp is mandatory for action requests to prevent PID reuse races.

Force End Task invokes `psutil.Process.terminate()` on Windows and then waits up to five seconds for exit. Tree termination is separate and is never implicit. Graceful close is conservatively reported as unsupported in the current agent rather than mislabeling `terminate()` as a GUI close request; proper Windows `WM_CLOSE` integration is an environment-dependent follow-up.

Protection includes the agent process, PID 0/4, core Windows names, PID/creation-time mismatch, access denied, and unavailable processes. Process names are only one signal; identity and access checks are primary. The agent never escalates privileges or bypasses protected-process controls.

