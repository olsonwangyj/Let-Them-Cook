import XCTest
@testable import Week7Bridge

final class ConfigurationTests: XCTestCase {
    func testConfigurationNeverSerializesPasswordFields() throws {
        let config = PublicConfiguration(boardUser: "board-user", jumpUser: "jump-user", useJump: true)
        let data = try JSONEncoder().encode(config)
        let fields = try XCTUnwrap(JSONSerialization.jsonObject(with: data) as? [String: Any])
        XCTAssertEqual(Set(fields.keys), ["boardUser", "jumpUser", "useJump"])
        XCTAssertEqual(try JSONDecoder().decode(PublicConfiguration.self, from: data), config)
    }

    func testRejectsPrivateKeysAndUnrelatedCertificate() throws {
        XCTAssertThrowsError(try AuthorityImport.validate("-----BEGIN PRIVATE KEY-----\nx\n-----END PRIVATE KEY-----"))
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        let unrelated = try String(contentsOf: root.appendingPathComponent("reference/teammate-localhost-cert.pem"))
        XCTAssertThrowsError(try AuthorityImport.validate(unrelated)) { error in
            guard case SetupError.wrongAuthority = error else { return XCTFail("Expected enrolled-CA mismatch") }
        }
        XCTAssertThrowsError(try AuthorityImport.validate("not a certificate"))
        XCTAssertThrowsError(try AuthorityImport.validate(String(repeating: "a", count: 65_537)))
    }

    func testRejectsMissingUsernamesAndControlCharacters() throws {
        XCTAssertThrowsError(try PublicConfiguration(boardUser: "", jumpUser: "u", useJump: true).validate())
        XCTAssertThrowsError(try PublicConfiguration(boardUser: "u\n", jumpUser: "u", useJump: true).validate())
        XCTAssertThrowsError(try PublicConfiguration(boardUser: "u", jumpUser: "", useJump: true).validate())
        XCTAssertNoThrow(try PublicConfiguration(boardUser: "u", jumpUser: "", useJump: false).validate())
    }
}
