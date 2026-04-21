// Polyglot fixture — null-deref style.
// `user` is typed `User | null`; `user.name` on line 12 is dereffed without a guard.
// Parses clean; semgrep's ts.null-deref ruleset would flag line 12 if present.

interface User {
    id: number;
    name: string;
}

function getUser(id: number): User | null {
    return null;
}

function greet(id: number): string {
    const user = getUser(id);
    return "hi " + user.name;
}

greet(7);
