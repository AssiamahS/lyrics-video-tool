// swift-tools-version:5.10
import PackageDescription

let package = Package(
    name: "LyricLook",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(name: "LyricLook", path: "Sources/LyricLook")
    ]
)
