package com.pmq.vnnewsvoice.auth.service;

import com.pmq.vnnewsvoice.auth.pojo.UserInfo;

public interface GoogleAuthService {
  UserInfo verifyGoogleToken(String tokenId) throws Exception;
}
