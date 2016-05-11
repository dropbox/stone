    let accessToken : DropboxAccessToken
    static var version = "InternalVersion"

    /// Shared instance for convenience
    public static var sharedClient : DropboxClient!

    public override func additionalHeaders(noauth : Bool) -> [String: String] {
        var headers = ["User-Agent": "OfficialDropboxSwiftSDKv2/\(DropboxClient.version)"]
        if (!noauth) {
            headers["Authorization"] = "Bearer \(self.accessToken)"
        }
        return headers
    }

    public convenience init(accessToken: DropboxAccessToken) {
        let manager = Manager(serverTrustPolicyManager: DropboxServerTrustPolicyManager())
        manager.startRequestsImmediately = false

        let backgroundConfig = NSURLSessionConfiguration.backgroundSessionConfigurationWithIdentifier("com.dropbox.SwiftyDropbox")
        let backgroundManager = Manager(configuration: backgroundConfig, serverTrustPolicyManager: DropboxServerTrustPolicyManager())
        backgroundManager.startRequestsImmediately = false

        self.init(accessToken: accessToken,
                  manager: manager,
                  backgroundManager: backgroundManager,
                  baseHosts: [
                        "meta"    : "https://api.dropbox.com/2",
                        "content" : "https://api-content.dropbox.com/2",
                        "notify"  : "https://notify.dropboxapi.com/2"
                  ])
    }
