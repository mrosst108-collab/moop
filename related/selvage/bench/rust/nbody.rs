fn energy(x: &[f64; 5], y: &[f64; 5], z: &[f64; 5], vx: &[f64; 5], vy: &[f64; 5], vz: &[f64; 5], m: &[f64; 5]) -> f64 {
    let mut e = 0.0;
    for i in 0..5 {
        e = e + 0.5 * m[i] * (vx[i] * vx[i] + vy[i] * vy[i] + vz[i] * vz[i]);
        for j in i + 1..5 {
            let (dx, dy, dz) = (x[i] - x[j], y[i] - y[j], z[i] - z[j]);
            e = e - m[i] * m[j] / (dx * dx + dy * dy + dz * dz).sqrt();
        }
    }
    e
}
fn main() {
    let pi = 3.141592653589793_f64; let solar = 4.0 * pi * pi; let year = 365.24;
    let mut x = [0.0, 4.84143144246472090e+00, 8.34336671824457987e+00, 1.28943695621391310e+01, 1.53796971148509165e+01];
    let mut y = [0.0, -1.16032004402742839e+00, 4.12479856412430479e+00, -1.51111514016986312e+01, -2.59193146099879641e+01];
    let mut z = [0.0, -1.03622044471123109e-01, -4.03523417114321381e-01, -2.23307578892655734e-01, 1.79258772950371181e-01];
    let mut vx = [0.0, 1.66007664274403694e-03 * year, -2.76742510726862411e-03 * year, 2.96460137564761618e-03 * year, 2.68067772490389322e-03 * year];
    let mut vy = [0.0, 7.69901118419740425e-03 * year, 4.99852801234917238e-03 * year, 2.37847173959480950e-03 * year, 1.62824170038242295e-03 * year];
    let mut vz = [0.0, -6.90460016972063023e-05 * year, 2.30417297573763929e-05 * year, -2.96589568540237556e-05 * year, -9.51592254519715870e-05 * year];
    let m = [solar, 9.54791938424326609e-04 * solar, 2.85885980666130812e-04 * solar, 4.36624404335156298e-05 * solar, 5.15138902046611451e-05 * solar];
    let (mut px, mut py, mut pz) = (0.0, 0.0, 0.0);
    for i in 0..5 { px = px + vx[i] * m[i]; py = py + vy[i] * m[i]; pz = pz + vz[i] * m[i]; }
    vx[0] = -px / solar; vy[0] = -py / solar; vz[0] = -pz / solar;
    let e0 = energy(&x, &y, &z, &vx, &vy, &vz, &m);
    for _ in 0..10_000_000 {
        for i in 0..5 {
            for j in i + 1..5 {
                let (dx, dy, dz) = (x[i] - x[j], y[i] - y[j], z[i] - z[j]);
                let d2 = dx * dx + dy * dy + dz * dz;
                let mag = 0.01 / (d2 * d2.sqrt());
                vx[i] = vx[i] - dx * m[j] * mag; vy[i] = vy[i] - dy * m[j] * mag; vz[i] = vz[i] - dz * m[j] * mag;
                vx[j] = vx[j] + dx * m[i] * mag; vy[j] = vy[j] + dy * m[i] * mag; vz[j] = vz[j] + dz * m[i] * mag;
            }
        }
        for i in 0..5 { x[i] = x[i] + 0.01 * vx[i]; y[i] = y[i] + 0.01 * vy[i]; z[i] = z[i] + 0.01 * vz[i]; }
    }
    println!("{}\n{}", e0, energy(&x, &y, &z, &vx, &vy, &vz, &m));
}
