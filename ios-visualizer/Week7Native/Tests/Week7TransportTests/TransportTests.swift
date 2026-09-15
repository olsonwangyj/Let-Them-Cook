import XCTest
import Foundation
import NIOCore
import NIOEmbedded
import NIOTLS
@testable import Week7Transport

final class TransportTests: XCTestCase {
    static var pki: TestPKI!
    override class func setUp() { super.setUp(); pki = try! TestPKI() }
    override class func tearDown() { pki = nil; super.tearDown() }

    // Removing either nested SSH hop, pin verification, TLS, or SUBSCRIBE prevents this result.
    func testTwoHopSSHThenVerifiedTLSDeliversResult() throws {
        let peers = try LocalPeers(pki: Self.pki)
        let got = expectation(description: "validated result")
        let client = Week7Client(route: peers.route(), session: "week7-demo", options: peers.options, onStatus: { _ in }, onResult: {
            XCTAssertEqual($0.resultID, "1:7:42"); XCTAssertEqual($0.gesture, "OPEN"); got.fulfill()
        })
        client.start(); wait(for: [got], timeout: 4); client.stop()
        XCTAssertEqual(peers.subscriptionCount, 1)
        XCTAssertEqual(peers.invalidSubscriptions, 0)
    }

    func testDirectSSHRouteAlsoDeliversResult() throws {
        let peers = try LocalPeers(pki: Self.pki)
        let got = expectation(description: "direct result")
        let client = Week7Client(route: peers.route(twoHop: false), session: "week7-demo", options: peers.options, onStatus: { _ in }, onResult: { _ in got.fulfill() })
        client.start(); wait(for: [got], timeout: 4); client.stop()
        XCTAssertEqual(peers.subscriptionCount, 1)
    }

    func testFailedIPv6CandidateDoesNotCancelSuccessfulIPv4SSHConnection() throws {
        let peers = try LocalPeers(pki: Self.pki)
        let normal = peers.route(twoHop: false)
        let route = SSHRoute(boardHost: "dual-stack.fixture", boardUser: normal.boardUser, boardPassword: normal.boardPassword, boardHostKey: normal.boardHostKey, caPEM: normal.caPEM)
        var options = peers.options; options.resolver = DualStackResolver(loop: peers.group.next())
        let got = expectation(description: "IPv4 fallback result")
        let client = Week7Client(route: route, session: "week7-demo", options: options, onStatus: { _ in }, onResult: { _ in got.fulfill() })
        client.start(); wait(for: [got], timeout: 4); client.stop()
        XCTAssertEqual(peers.subscriptionCount, 1)
    }

    func testCancellationClosesEveryAllocatedConnectionCandidate() throws {
        let loop = EmbeddedEventLoop()
        let first = EmbeddedChannel(loop: loop)
        let second = EmbeddedChannel(loop: loop)
        let attempt = ConnectionAttempt()
        attempt.register(first); attempt.register(second)
        var closed = 0
        first.closeFuture.whenSuccess { closed += 1 }
        second.closeFuture.whenSuccess { closed += 1 }
        attempt.cancel(); loop.run()
        XCTAssertEqual(closed, 2)
        _ = try first.finish(acceptAlreadyClosed: true)
        _ = try second.finish(acceptAlreadyClosed: true)
    }

    func testUnenrolledBoardHostKeyCannotSubscribe() throws {
        let peers = try LocalPeers(pki: Self.pki)
        try assertRejected(peers, route: peers.route(badBoardKey: true))
        XCTAssertEqual(peers.subscriptionCount, 0)
    }

    func testUnenrolledJumpHostKeyCannotSubscribe() throws {
        let peers = try LocalPeers(pki: Self.pki)
        try assertRejected(peers, route: peers.route(badJumpKey: true))
        XCTAssertEqual(peers.subscriptionCount, 0)
    }

    func testExpiredTrustedCertificateCannotSubscribe() throws {
        let expired = try TestPKI(expired: true)
        let peers = try LocalPeers(pki: expired)
        try assertRejected(peers, route: peers.route())
        XCTAssertEqual(peers.subscriptionCount, 0)
    }

    func testStopDuringStalledSSHHandshakeClosesAllocatedRoot() throws {
        let accepted = expectation(description: "SSH root accepted")
        let peers = try LocalPeers(pki: Self.pki, stallSSH: true, onSSHConnection: { accepted.fulfill() })
        let retired = expectation(description: "retired result"); retired.isInverted = true
        let client = Week7Client(route: peers.route(), session: "week7-demo", options: peers.options, onStatus: { _ in }, onResult: { _ in retired.fulfill() })
        client.start(); wait(for: [accepted], timeout: 3); client.stop()
        wait(for: [retired], timeout: 0.5)
        XCTAssertEqual(peers.connections.activeCount, 0)
        XCTAssertEqual(peers.subscriptionCount, 0)
    }

    func testFixtureListenersAndTemporaryAuthorityAreReleased() throws {
        var pki: TestPKI? = try TestPKI()
        let directory = pki!.directory
        var peers: LocalPeers? = try LocalPeers(pki: pki!)
        weak var reference = peers
        peers = nil
        XCTAssertTrue(reference == nil)
        reference = nil
        pki = nil
        XCTAssertFalse(FileManager.default.fileExists(atPath: directory.path))
    }

    func testWrongPasswordCannotSubscribe() throws {
        let peers = try LocalPeers(pki: Self.pki)
        try assertRejected(peers, route: peers.route(password: "rejected-fixture-password"))
        XCTAssertEqual(peers.subscriptionCount, 0)
    }

    func testWrongPasswordIdentifiesEachHopAndDoesNotAutomaticallyRetry() throws {
        for jumpHop in [false, true] {
            let peers = try LocalPeers(pki: Self.pki)
            let normal = peers.route()
            let jump = try XCTUnwrap(normal.jump)
            let route = SSHRoute(boardHost: normal.boardHost, boardUser: normal.boardUser,
                                 boardPassword: jumpHop ? normal.boardPassword : "rejected-fixture-password", boardHostKey: normal.boardHostKey,
                                 jump: .init(host: jump.host, user: jump.user,
                                             password: jumpHop ? "rejected-fixture-password" : jump.password, hostKey: jump.hostKey), caPEM: normal.caPEM)
            let rejected = expectation(description: "identified terminal rejection")
            let repeated = expectation(description: "credentials retried"); repeated.isInverted = true; repeated.assertForOverFulfill = false
            let lock = NSLock(); var rejectedOnce = false
            let client = Week7Client(route: route, session: "week7-demo", options: peers.options, onStatus: { status in
                lock.lock(); defer { lock.unlock() }
                if rejectedOnce { repeated.fulfill() }
                else if status.hasPrefix("Disconnected") {
                    XCTAssertEqual(status, "Disconnected: \(jumpHop ? "Jump host" : "Board") did not accept password authentication; correct setup and reconnect")
                    rejectedOnce = true; rejected.fulfill()
                }
            }, onResult: { _ in XCTFail("Rejected authentication delivered a result") })
            client.start(); wait(for: [rejected], timeout: 4)
            wait(for: [repeated], timeout: 0.3); client.stop()
            XCTAssertEqual(peers.subscriptionCount, 0)
        }
    }

    func testAuthenticationAndTrustFailuresDoNotAutomaticallyRetryCredentials() throws {
        let unrelated = try TestPKI()
        let peers = try LocalPeers(pki: Self.pki)
        for route in [peers.route(password: "rejected-fixture-password"), peers.route(badBoardKey: true), peers.route(ca: unrelated.ca)] {
            let rejected = expectation(description: "terminal rejection")
            let repeated = expectation(description: "credentials retried"); repeated.isInverted = true; repeated.assertForOverFulfill = false
            let lock = NSLock(); var rejectedOnce = false
            let client = Week7Client(route: route, session: "week7-demo", options: peers.options, onStatus: { status in
                lock.lock(); defer { lock.unlock() }
                if rejectedOnce { repeated.fulfill() }
                else if status.hasPrefix("Disconnected") { rejectedOnce = true; rejected.fulfill() }
            }, onResult: { _ in XCTFail("untrusted result") })
            client.start(); wait(for: [rejected], timeout: 4)
            wait(for: [repeated], timeout: 0.3); client.stop()
        }
    }

    func testEstablishedFrameFirstByteDoesNotExtendItsFiveSecondDeadline() throws {
        let loop = EmbeddedEventLoop()
        let channel = EmbeddedChannel(loop: loop)
        var failures = 0
        let handler = Subscriber(session: "week7-demo", options: TransportOptions(), firstResult: { false }, onSubscribed: {}, onResult: { _ in }, onFailure: { _ in failures += 1 })
        try channel.pipeline.syncOperations.addHandler(handler)
        channel.pipeline.fireUserInboundEventTriggered(TLSUserEvent.handshakeCompleted(negotiatedProtocol: nil))
        var ack = channel.allocator.buffer(capacity: 100)
        ack.writeInteger(UInt32(LocalPeers.ack.utf8.count)); ack.writeString(LocalPeers.ack)
        _ = try channel.writeInbound(ack)
        loop.advanceTime(by: .seconds(4))
        var firstByte = channel.allocator.buffer(capacity: 1); firstByte.writeInteger(UInt8(0))
        _ = try channel.writeInbound(firstByte)
        loop.advanceTime(by: .seconds(1))
        XCTAssertEqual(failures, 1, "The initial byte cannot restart an established frame deadline")
        _ = try channel.finish(acceptAlreadyClosed: true)
    }

    func testUnrelatedCACannotSubscribe() throws {
        let unrelated = try TestPKI()
        let peers = try LocalPeers(pki: Self.pki)
        try assertRejected(peers, route: peers.route(ca: unrelated.ca))
        XCTAssertEqual(peers.subscriptionCount, 0)
    }

    func testTrustedCertificateWithWrongHostnameCannotSubscribe() throws {
        let wrongName = try TestPKI(hostname: "wrong.week7.internal")
        let peers = try LocalPeers(pki: wrongName)
        try assertRejected(peers, route: peers.route())
        XCTAssertEqual(peers.subscriptionCount, 0)
    }

    func testResultBeforeSubscribedAndMalformedResultAreRejected() throws {
        for behavior in [LocalPeers.Behavior.resultBeforeAck, .malformedResult] {
            let peers = try LocalPeers(pki: Self.pki, behavior: behavior)
            try assertRejected(peers, route: peers.route())
            XCTAssertGreaterThan(peers.subscriptionCount, 0)
        }
    }

    func testPartialPrefixAndBodyUseFrameDeadlineAfterFirstByte() throws {
        for behavior in [LocalPeers.Behavior.partialPrefix, .partialBody] {
            let peers = try LocalPeers(pki: Self.pki, behavior: behavior)
            let failed = expectation(description: "partial frame expires")
            let got = expectation(description: "no partial result"); got.isInverted = true
            let client = Week7Client(route: peers.route(), session: "week7-demo", options: peers.options, onStatus: { status in
                if status.contains("frame deadline") { failed.fulfill() }
            }, onResult: { _ in got.fulfill() })
            client.start(); wait(for: [failed], timeout: 3); client.stop()
            wait(for: [got], timeout: 0.1)
        }
    }

    func testIdleFirstResultUsesLongerGraceThenCloses() throws {
        let peers = try LocalPeers(pki: Self.pki, behavior: .idle)
        let subscribed = expectation(description: "subscribed")
        let failure = expectation(description: "first result deadline")
        let lock = NSLock(); var began: Date?; var elapsed = 0.0
        let client = Week7Client(route: peers.route(), session: "week7-demo", options: peers.options, onStatus: { status in
            lock.lock(); defer { lock.unlock() }
            if status == "Subscribed" { began = Date(); subscribed.fulfill() }
            if status.contains("frame deadline"), let began { elapsed = Date().timeIntervalSince(began); failure.fulfill() }
        }, onResult: { _ in XCTFail("idle peer delivered result") })
        client.start(); wait(for: [subscribed, failure], timeout: 3); client.stop()
        lock.lock(); let duration = elapsed; lock.unlock()
        XCTAssertGreaterThan(duration, 0.45)
        XCTAssertLessThan(duration, 1.4)
    }

    func testConnectionRecoveryResubscribesExactlyOncePerConnection() throws {
        let peers = try LocalPeers(pki: Self.pki, behavior: .closeFirst)
        let got = expectation(description: "result after reconnect")
        let client = Week7Client(route: peers.route(), session: "week7-demo", options: peers.options, onStatus: { _ in }, onResult: { _ in got.fulfill() })
        client.start(); wait(for: [got], timeout: 4); client.stop()
        XCTAssertEqual(peers.subscriptionCount, 2)
        XCTAssertEqual(peers.invalidSubscriptions, 0)
    }

    func testTemporaryDirectForwardFailureReconnects() throws {
        let peers = try LocalPeers(pki: Self.pki, rejectFirstForward: true)
        let got = expectation(description: "result after direct forwarding recovers")
        let client = Week7Client(route: peers.route(), session: "week7-demo", options: peers.options, onStatus: { _ in }, onResult: { _ in got.fulfill() })
        client.start(); wait(for: [got], timeout: 4); client.stop()
        XCTAssertEqual(peers.subscriptionCount, 1)
    }

    func testOuterSSHConnectionLossReconnectsEntireRoute() throws {
        let peers = try LocalPeers(pki: Self.pki)
        let got = expectation(description: "result before and after root loss"); got.expectedFulfillmentCount = 2
        let lock = NSLock(); var count = 0
        let client = Week7Client(route: peers.route(), session: "week7-demo", options: peers.options, onStatus: { _ in }, onResult: { _ in
            lock.lock(); count += 1; let first = count == 1; lock.unlock()
            got.fulfill()
            if first { peers.closeConnections() }
        })
        client.start(); wait(for: [got], timeout: 4); client.stop()
        XCTAssertEqual(peers.subscriptionCount, 2)
    }

    func testRepeatedSubscribedButIdleConnectionsBackOffUntilValidResult() throws {
        let peers = try LocalPeers(pki: Self.pki, behavior: .idle)
        var options = peers.options
        options.firstResultTimeout = .milliseconds(40)
        options.frameTimeout = .milliseconds(40)
        options.retryMaximum = .milliseconds(200)
        let subscribed = expectation(description: "four subscriptions"); subscribed.expectedFulfillmentCount = 4
        let lock = NSLock(); var times: [Double] = []
        let client = Week7Client(route: peers.route(), session: "week7-demo", options: options, onStatus: { status in
            if status == "Subscribed" {
                lock.lock(); times.append(ProcessInfo.processInfo.systemUptime); lock.unlock()
                subscribed.fulfill()
            }
        }, onResult: { _ in XCTFail("idle peer returned result") })
        client.start(); wait(for: [subscribed], timeout: 4); client.stop()
        lock.lock(); let observed = times; lock.unlock()
        XCTAssertEqual(observed.count, 4)
        if observed.count == 4 { XCTAssertGreaterThanOrEqual(observed[3] - observed[2], 0.23) }
    }

    func testStopDuringLiveStreamClosesOwnedTwoHopConnectionAndSuppressesCallbacks() throws {
        let peers = try LocalPeers(pki: Self.pki)
        let got = expectation(description: "result")
        let retired = expectation(description: "retired callback"); retired.isInverted = true
        let lock = NSLock(); var stopped = false
        let client = Week7Client(route: peers.route(), session: "week7-demo", options: peers.options, onStatus: { _ in
            lock.lock(); defer { lock.unlock() }; if stopped { retired.fulfill() }
        }, onResult: { _ in
            lock.lock(); defer { lock.unlock() }; if stopped { retired.fulfill() } else { got.fulfill() }
        })
        client.start(); wait(for: [got], timeout: 4); client.stop()
        lock.lock(); stopped = true; lock.unlock()
        wait(for: [retired], timeout: 0.8)
        XCTAssertEqual(peers.connections.activeCount, 0)
        XCTAssertEqual(peers.subscriptionCount, 1)
    }

    func testImmediateStopPreventsConnectionAndFutureCallbacks() throws {
        let peers = try LocalPeers(pki: Self.pki)
        let retired = expectation(description: "retired result"); retired.isInverted = true
        let client = Week7Client(route: peers.route(), session: "week7-demo", options: peers.options, onStatus: { _ in }, onResult: { _ in retired.fulfill() })
        client.start(); client.stop()
        wait(for: [retired], timeout: 0.5)
        XCTAssertEqual(peers.connections.activeCount, 0)
        XCTAssertEqual(peers.subscriptionCount, 0)
    }

    private func assertRejected(_ peers: LocalPeers, route: SSHRoute) throws {
        let failure = expectation(description: "connection rejected")
        let got = expectation(description: "untrusted result"); got.isInverted = true
        let client = Week7Client(route: route, session: "week7-demo", options: peers.options, onStatus: { status in
            if status.hasPrefix("Disconnected") { failure.fulfill() }
        }, onResult: { _ in got.fulfill() })
        client.start(); wait(for: [failure], timeout: 4); client.stop()
        wait(for: [got], timeout: 0.1)
    }
}
