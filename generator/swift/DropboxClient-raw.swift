	let accessToken : DropboxAccessToken

	/// Shared instance for convenience
	public static var sharedClient : DropboxClient!

	public override func additionalHeaders(noauth : Bool) -> [String: String] {
		var headers = ["User-Agent": "OfficialDropboxSwiftSDKv2/0.7.1"]
		if (!noauth) {
			headers["Authorization"] = "Bearer \(self.accessToken)"
		}
		return headers
	}

	public convenience init(accessToken: DropboxAccessToken) {
		let manager = Manager(serverTrustPolicyManager: DropboxServerTrustPolicyManager())
		self.init(accessToken: accessToken,
				  manager: manager,
				  baseHosts: [
		              "meta"    : "https://api.dropbox.com/2",
		              "content" : "https://api-content.dropbox.com/2",
		              "notify"  : "https://notify.dropboxapi.com/2"
		          ])
	}
