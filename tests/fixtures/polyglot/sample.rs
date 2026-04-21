// Polyglot fixture — Option::unwrap() panic path.
// `head()` returns Option<i32>; line 10 unwraps on an empty vec.
// Parses clean; clippy::unwrap_used would flag line 10.

fn head(xs: &Vec<i32>) -> Option<i32> {
    xs.first().copied()
}

fn main() {
    let empty: Vec<i32> = Vec::new();
    let v = head(&empty).unwrap();
    println!("{}", v);
}
