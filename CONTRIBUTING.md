# Contributing

Issues and focused pull requests are welcome.

1. Describe the gateway version and the policy behavior being modeled.
2. Add a deterministic fixture and at least one test.
3. Keep provider calls out of unit tests.
4. Run `python -m unittest discover -s tests -v`, `python -m compileall -q src tests`, and the benchmark command before submitting.
5. Document any new metadata assumption, adapter limitation, or license obligation.

Please do not submit real prompts, credentials, customer configuration, provider responses, or proprietary traces.
