import XCTest
import NIOCore
import NIOEmbedded
import NIOSSH
@testable import Week7Transport

final class TrustTests: XCTestCase {
    let board = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIC7by9bvClMnRjk3KKoR+QpRdhuUXhIhVPC1+F2FnV39"
    let other = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILfypXFWxIhmHZ1nZZKsNKIYRZvnXrra4sqWpnBRy66i"

    func testRevocationPreventsDeferredAuthenticationFromRecoveringEitherPassword() {
        let credentials = CredentialVault(board: "isolated-board-fixture", jump: "isolated-jump-fixture")
        let deferred = credentials
        credentials.clear()
        XCTAssertTrue(deferred.password(jumpHop: false) == nil)
        XCTAssertTrue(deferred.password(jumpHop: true) == nil)
    }

    func testAuthDelegateCannotOfferPasswordAfterVaultRevocation() throws {
        let loop = EmbeddedEventLoop()
        let credentials = CredentialVault(board: "isolated-board-fixture", jump: nil)
        let authentication = PasswordAuthentication(username: "fixture", credentials: credentials, jumpHop: false)
        credentials.clear()
        let offer = loop.makePromise(of: NIOSSHUserAuthenticationOffer?.self)
        authentication.nextAuthenticationType(availableMethods: .password, nextChallengePromise: offer)
        XCTAssertThrowsError(try offer.futureResult.wait())
    }

    // A server with a valid but unenrolled key must not pass authentication.
    func testExactHostKeyRejectsDifferentValidKey() throws {
        let loop = EmbeddedEventLoop()
        let check = try PinnedHostKey(board)
        let accepted = loop.makePromise(of: Void.self)
        check.validateHostKey(hostKey: try NIOSSHPublicKey(openSSHPublicKey: board), validationCompletePromise: accepted)
        XCTAssertNoThrow(try accepted.futureResult.wait())
        let rejected = loop.makePromise(of: Void.self)
        check.validateHostKey(hostKey: try NIOSSHPublicKey(openSSHPublicKey: other), validationCompletePromise: rejected)
        XCTAssertThrowsError(try rejected.futureResult.wait())
    }
}
