#[derive(Clone, Copy)] struct Phase { q: i64, p: i64 }
fn orbit(k: i64, steps: i64, mut s: Phase) -> Phase {
    for _ in 0..steps { s.p -= k * s.q / 2000; s.q += s.p; s.p -= k * s.q / 2000; }
    s
}
fn orbit_inv(k: i64, steps: i64, mut s: Phase) -> Phase {
    for _ in 0..steps { s.p += k * s.q / 2000; s.q -= s.p; s.p += k * s.q / 2000; }
    s
}
fn main() {
    let s = orbit(10, 100_000_000, Phase { q: 100000, p: 0 });
    println!("Phase({}, {})", s.q, s.p);
    let b = orbit_inv(10, 100_000_000, s);
    println!("Phase({}, {})", b.q, b.p);
}
