#if os(iOS)
import UIKit
import UniformTypeIdentifiers

final class SetupViewController: UIViewController, UIDocumentPickerDelegate {
    var onConnect: ((PublicConfiguration, String, String, String) throws -> Void)?
    var onDisconnect: (() -> Void)?
    private let boardUser = UITextField(), boardPassword = UITextField()
    private let jumpUser = UITextField(), jumpPassword = UITextField()
    private let useJump = UISwitch()
    private let certificate = UILabel(), notice = UILabel()
    private var caPEM: String?
    private let configuration: PublicConfiguration
    private let initiallyConnected: Bool

    init(configuration: PublicConfiguration, caPEM: String?, connected: Bool) {
        self.configuration = configuration; self.caPEM = caPEM; initiallyConnected = connected
        super.init(nibName: nil, bundle: nil)
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) is unavailable") }

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Week 7 Visualizer"
        view.backgroundColor = .systemBackground
        navigationItem.rightBarButtonItem = UIBarButtonItem(barButtonSystemItem: .done, target: self, action: #selector(done))
        let scroll = UIScrollView(); scroll.keyboardDismissMode = .interactive
        scroll.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(scroll)
        let stack = UIStackView(); stack.axis = .vertical; stack.spacing = 12
        stack.translatesAutoresizingMaskIntoConstraints = false
        scroll.addSubview(stack)
        NSLayoutConstraint.activate([
            scroll.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor),
            scroll.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor),
            scroll.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            scroll.bottomAnchor.constraint(equalTo: view.keyboardLayoutGuide.topAnchor),
            stack.leadingAnchor.constraint(equalTo: scroll.contentLayoutGuide.leadingAnchor, constant: 20),
            stack.trailingAnchor.constraint(equalTo: scroll.contentLayoutGuide.trailingAnchor, constant: -20),
            stack.topAnchor.constraint(equalTo: scroll.contentLayoutGuide.topAnchor, constant: 16),
            stack.bottomAnchor.constraint(equalTo: scroll.contentLayoutGuide.bottomAnchor, constant: -24),
            stack.widthAnchor.constraint(equalTo: scroll.frameLayoutGuide.widthAnchor, constant: -40)
        ])
        func label(_ text: String, small: Bool = false) -> UILabel {
            let label = UILabel(); label.text = text; label.numberOfLines = 0
            label.font = .preferredFont(forTextStyle: small ? .footnote : .body)
            label.adjustsFontForContentSizeCategory = true
            if small { label.textColor = .secondaryLabel }
            return label
        }
        stack.addArrangedSubview(label("DUMMY gestures · session week7-demo"))
        stack.addArrangedSubview(label("The iPhone connects through its own SSH session. Keep the app in the foreground. Leaving the app stops reception and clears passwords.", small: true))
        stack.addArrangedSubview(label("Board: \(EnrolledTrust.boardHost)", small: true))
        func field(_ field: UITextField, name: String, value: String = "", secret: Bool = false) {
            field.borderStyle = .roundedRect; field.placeholder = name; field.text = value
            field.isSecureTextEntry = secret; field.autocorrectionType = .no
            field.autocapitalizationType = .none; field.spellCheckingType = .no
            field.textContentType = secret ? .password : .username
            field.accessibilityLabel = name; field.accessibilityIdentifier = "week7." + name.replacingOccurrences(of: " ", with: "")
            field.heightAnchor.constraint(greaterThanOrEqualToConstant: 44).isActive = true
            stack.addArrangedSubview(field)
        }
        field(boardUser, name: "Board username", value: configuration.boardUser)
        field(boardPassword, name: "Board password", secret: true)
        let jumpRow = UIStackView(arrangedSubviews: [label("Use campus jump host"), useJump])
        jumpRow.axis = .horizontal; useJump.isOn = configuration.useJump
        useJump.addTarget(self, action: #selector(updateJump), for: .valueChanged)
        stack.addArrangedSubview(jumpRow)
        stack.addArrangedSubview(label("Jump host: \(EnrolledTrust.jumpHost)", small: true))
        field(jumpUser, name: "Jump username", value: configuration.jumpUser)
        field(jumpPassword, name: "Jump password", secret: true)
        updateJump()
        certificate.font = .preferredFont(forTextStyle: .footnote); certificate.numberOfLines = 0
        stack.addArrangedSubview(certificate); updateCertificate()
        func action(_ title: String, handler: @escaping () -> Void) {
            let button = UIButton(type: .system)
            var style = UIButton.Configuration.filled(); style.title = title
            button.configuration = style
            button.addAction(UIAction { _ in handler() }, for: .touchUpInside)
            button.heightAnchor.constraint(greaterThanOrEqualToConstant: 44).isActive = true
            stack.addArrangedSubview(button)
        }
        action("Import verified public CA") { [weak self] in self?.chooseCA() }
        notice.text = initiallyConnected ? "A session is active. Connect restarts it; Disconnect stops it." : "Enter passwords when ready to connect."
        notice.numberOfLines = 0; notice.font = .preferredFont(forTextStyle: .footnote)
        stack.addArrangedSubview(notice)
        action("Connect") { [weak self] in self?.connect() }
        action("Disconnect") { [weak self] in self?.onDisconnect?(); self?.clearPasswords(); self?.notice.text = "Disconnected" }
    }

    @objc private func updateJump() {
        jumpUser.isEnabled = useJump.isOn; jumpPassword.isEnabled = useJump.isOn
        if !useJump.isOn { jumpPassword.text = nil }
    }
    @objc private func done() { clearPasswords(); dismiss(animated: true) }
    func clearPasswords() { boardPassword.text = nil; jumpPassword.text = nil }
    override func viewDidDisappear(_ animated: Bool) { super.viewDidDisappear(animated); clearPasswords() }

    private func updateCertificate() {
        certificate.text = caPEM == nil ? "CA not imported. Only the enrolled public Week 7 CA is accepted." : "Verified Week 7 CA imported.\nSHA-256: \(EnrolledTrust.caSHA256)"
    }
    private func chooseCA() {
        clearPasswords()
        let picker = UIDocumentPickerViewController(forOpeningContentTypes: [.data], asCopy: true)
        picker.delegate = self; picker.allowsMultipleSelection = false
        present(picker, animated: true)
    }
    func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
        guard let url = urls.first else { return }
        let access = url.startAccessingSecurityScopedResource()
        defer { if access { url.stopAccessingSecurityScopedResource() } }
        do {
            let handle = try FileHandle(forReadingFrom: url); defer { try? handle.close() }
            let data = try handle.read(upToCount: 65_537) ?? Data()
            guard data.count <= 65_536, let pem = String(data: data, encoding: .utf8) else { throw SetupError.certificate }
            caPEM = try AuthorityImport.validate(pem)
            updateCertificate(); notice.text = "CA verified. Enter passwords and connect."
        } catch {
            notice.text = (error as? SetupError)?.localizedDescription ?? "Could not read this file. Import the verified public CA PEM."
        }
    }
    private func connect() {
        do {
            let config = PublicConfiguration(boardUser: boardUser.text ?? "", jumpUser: jumpUser.text ?? "", useJump: useJump.isOn)
            try config.validate()
            guard let ca = caPEM else { throw SetupError.certificate }
            guard let password = boardPassword.text, !password.isEmpty,
                  !config.useJump || !(jumpPassword.text ?? "").isEmpty else {
                notice.text = "Enter the required passwords. They remain in memory only."; return
            }
            try onConnect?(config, ca, password, jumpPassword.text ?? "")
            clearPasswords(); dismiss(animated: true)
        } catch {
            notice.text = (error as? SetupError)?.localizedDescription ?? "Could not save the public setup. Try again while the iPhone is unlocked."
        }
    }
}
#endif
