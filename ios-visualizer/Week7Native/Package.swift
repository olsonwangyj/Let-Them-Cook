// swift-tools-version: 5.10
import PackageDescription

let package = Package(
    name: "Week7Native",
    platforms: [.iOS(.v15), .macOS(.v13)],
    products: [.library(name: "Week7Native", type: .static, targets: ["Week7Bridge"])],
    dependencies: [
        .package(url: "https://github.com/apple/swift-nio.git", exact: "2.102.0"),
        .package(url: "https://github.com/apple/swift-nio-ssh.git", exact: "0.15.0"),
        .package(url: "https://github.com/apple/swift-nio-ssl.git", exact: "2.37.4"),
        .package(url: "https://github.com/apple/swift-crypto.git", exact: "4.5.2"),
    ],
    targets: [
        .target(name: "Week7Core"),
        .target(name: "Week7Transport", dependencies: ["Week7Core",
            .product(name: "NIOCore", package: "swift-nio"),
            .product(name: "NIOPosix", package: "swift-nio"),
            .product(name: "NIOTLS", package: "swift-nio"),
            .product(name: "NIOSSH", package: "swift-nio-ssh"),
            .product(name: "NIOSSL", package: "swift-nio-ssl"),
            .product(name: "Crypto", package: "swift-crypto")]),
        .target(name: "Week7Bridge", dependencies: ["Week7Core", "Week7Transport"]),
        .testTarget(name: "Week7CoreTests", dependencies: ["Week7Core"]),
        .testTarget(name: "Week7BridgeTests", dependencies: ["Week7Bridge"]),
        .testTarget(name: "Week7TransportTests", dependencies: ["Week7Transport", "Week7Core",
            .product(name: "NIOEmbedded", package: "swift-nio"),
            .product(name: "NIOSSH", package: "swift-nio-ssh"),
            .product(name: "NIOSSL", package: "swift-nio-ssl"),
            .product(name: "Crypto", package: "swift-crypto")]),
    ]
)
