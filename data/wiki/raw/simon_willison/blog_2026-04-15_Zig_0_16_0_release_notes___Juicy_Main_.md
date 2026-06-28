# Zig 0.16.0 release notes: "Juicy Main"
url: https://simonwillison.net/2026/Apr/15/juicy-main/#atom-everything
author: Simon Willison
published_at: 2026-04-15
persona_id: simon_willison

---

Zig 0.16.0 release notes: "Juicy Main" Zig has really good release notes - comprehensive, detailed, and with relevant usage examples for each of the new features. Of particular note in the newly released Zig 0.16.0 is what they are calling "Juicy Main" - a dependency injection feature for your program's main() function where accepting a process.Init parameter grants access to a struct of useful properties: const std = @import ( "std" ); pub fn main ( init : std.process.Init ) ! void { /// general purpose allocator for temporary heap allocations: const gpa = init . gpa ; /// default Io implementation: const io = init . io ; /// access to environment variables: std . log . info ( "{d} env vars" , .{ init . environ_map . count ()}); /// access to CLI arguments const args = try init . minimal . args . toSlice ( init . arena . allocator () );
} Via Lobste.rs Tags: zig
