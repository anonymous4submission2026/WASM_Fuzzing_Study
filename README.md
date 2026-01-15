# WASM Bug Study Artifacts

This is an artifact repository for the paper titled **Left Behind, Not Forgotten: Reusing Regression Tests to Find Bugs in WebAssembly Runtimes**.

This paper reports on a large-scale study to assess the benefits of using regression tests to find bugs in WASM runtimes. The study explores two scenarios of use of regression tests: (1) transplanting such tests across runtimes and (2) using such tests as seed corpora for fuzzing. Our study revealed a total of 38 previously-unknown bugs across 3 WASM runtimes; 13 through transplantation and 25 through fuzzing. This number goes far beyond the number of bugs found through fuzzing using well-known seed corpora. Our findings yield both empirical observations and actionable recommendations.

Our mined seed corpora `rtbench` (acronym for *Regression Test Bench*) is shared in this repository's release artifacts. ([Link](https://github.com/anonymous4submission2026/WASM_Bug_Study/releases/download/submission/rtbench.tar.gz)).
