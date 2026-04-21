// Polyglot fixture — missing await / unhandled promise rejection.
// `fetchData()` returns a Promise; line 11 consumes it as if sync. No .catch, no try.
// Parses clean; semgrep's js.missing-await ruleset would flag line 11 if present.

function fetchData() {
    return Promise.reject(new Error("boom"));
}

function run() {
    const data = fetchData();
    console.log(data.value);
}

run();
