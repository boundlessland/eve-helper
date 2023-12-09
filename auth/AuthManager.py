import hashlib
import secrets
import time
from multiprocessing import Queue, Process
import urllib.parse

import requests
import base64
from auth.AuthServer import runServer
from util.DataLoader import loadConfigFromJSON, dumpConfigToJSON


class AuthManager:
    def __init__(self, commonConfigPath: str, privateConfigPath: str, authServerConfigPath: str):
        self.config = loadConfigFromJSON(commonConfigPath)
        self.config.update(loadConfigFromJSON(privateConfigPath))
        self.authServerConfig = loadConfigFromJSON(authServerConfigPath)

    def AddAuth(self):
        semaphore = Queue()
        receiver = Process(target=runServer, args=(self.authServerConfig, semaphore))
        receiver.start()
        while semaphore.empty():
            time.sleep(2)
        semaphore.get()
        codeVerifier = self.generateAuthorizeUrl()
        while semaphore.empty():
            time.sleep(2)
            continue
        authCode = semaphore.get()
        print(authCode)
        self.shutdownServer()
        receiver.join()
        self.getAccessToken(authCode, codeVerifier)
        return

    def AuthUpdater(self, authCode: dict):
        authTable = loadConfigFromJSON(self.config["auth_config_path"])
        authTable.update(authCode)
        dumpConfigToJSON(self.config["auth_config_path"], authTable)
        return

    def generateAuthorizeUrl(self):
        baseUrl = self.config["authorize_url"]
        # 这段加密是ccp提供的
        random = base64.urlsafe_b64encode(secrets.token_bytes(32))
        m = hashlib.sha256()
        m.update(random)
        d = m.digest()
        codeChallenge = base64.urlsafe_b64encode(d).decode().replace("=", "")
        codeVerifier = random

        params = [("response_type", "code"), ("redirect_uri", self.config["redirect_uri"]),
                  ("client_id", self.config["client_id"]), ("scope", self.config["scope"]),
                  ("code_challenge", codeChallenge), ("code_challenge_method", "S256"),
                  ("state", self.config["state"])]
        url = baseUrl + "?" + "&".join(f"{_[0]}={urllib.parse.quote(_[1])}" for _ in params)
        print(f"请点击此链接授权：{url}")
        return codeVerifier

    def shutdownServer(self):
        requests.get(self.config["shutdown_server"], verify=False)
        return

    def getAccessToken(self, authCode, codeVerifier):
        # cookies = {}
        # for cookie in self.config["cookie"].split(";"):
        #     kv = cookie.strip().split("=")
        #     cookies[kv[0]] = kv[1]
        # print(cookies)
        session = requests.Session()
        # session.cookies.update(cookies)
        url = self.config["authorize_token_url"]
        payload = {"grant_type": "authorization_code", "code": authCode, "client_id": self.config["client_id"],
                   "code_verifier": codeVerifier}
        headers = {"Content-Type": "application/x-www-form-urlencoded",
                   "Host": "login.eveonline.com"}
        response = session.post(url, data=payload, headers=headers)
        print(response.status_code)
        print(response.text)
        return


if __name__ == "__main__":
    a = AuthManager("../config/AuthSettings.json", "../config/privateAuthSettings.json", "../config/AuthServerConfig.json")
    a.AddAuth()
