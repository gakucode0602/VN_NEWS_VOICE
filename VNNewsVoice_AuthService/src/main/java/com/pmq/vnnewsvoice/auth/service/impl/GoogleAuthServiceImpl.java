package com.pmq.vnnewsvoice.auth.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.api.client.googleapis.auth.oauth2.GoogleIdToken;
import com.google.api.client.googleapis.auth.oauth2.GoogleIdTokenVerifier;
import com.google.api.client.http.javanet.NetHttpTransport;
import com.google.api.client.json.gson.GsonFactory;
import com.pmq.vnnewsvoice.auth.pojo.Reader;
import com.pmq.vnnewsvoice.auth.pojo.UserInfo;
import com.pmq.vnnewsvoice.auth.pojo.UserProvider;
import com.pmq.vnnewsvoice.auth.repository.UserProviderRepository;
import com.pmq.vnnewsvoice.auth.service.GoogleAuthService;
import com.pmq.vnnewsvoice.auth.service.ReaderService;
import com.pmq.vnnewsvoice.auth.service.RoleService;
import com.pmq.vnnewsvoice.auth.service.UserInfoService;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
@RequiredArgsConstructor
public class GoogleAuthServiceImpl implements GoogleAuthService {
  @Value("${GOOGLE_CLIENT_ID}")
  private String googleClientId;

  private final UserInfoService userInfoService;
  private final ReaderService readerService;
  private final RoleService roleService;
  private final UserProviderRepository userProviderRepository;
  private final BCryptPasswordEncoder bCryptPasswordEncoder;

  private final ObjectMapper objectMapper = new ObjectMapper();

  @Override
  public UserInfo verifyGoogleToken(String tokenId) throws Exception {
    GoogleIdTokenVerifier verifier =
        new GoogleIdTokenVerifier.Builder(new NetHttpTransport(), new GsonFactory())
            .setAudience(Collections.singletonList(googleClientId))
            .build();
    GoogleIdToken idToken = verifier.verify(tokenId);

    if (idToken == null) {
      throw new Exception("Invalid Google ID token");
    }

    GoogleIdToken.Payload payload = idToken.getPayload();
    String googleId = payload.getSubject();
    String email = payload.getEmail();
    String name = (String) payload.get("name");
    String pictureUrl = (String) payload.get("picture");

    Optional<UserProvider> existingProvider =
        userProviderRepository.findFirstByProviderIdAndProviderType(googleId, "GOOGLE");

    UserInfo userInfo;
    if (existingProvider.isPresent()) {
      userInfo = existingProvider.get().getUserId();
    } else {
      Optional<UserInfo> existingUser = userInfoService.getUserByEmail(email);
      if (existingUser.isPresent()) {
        userInfo = existingUser.get();
      } else {
        userInfo = new UserInfo();
        userInfo.setUsername(
            email.split("@")[0] + "_" + UUID.randomUUID().toString().substring(0, 8));
        userInfo.setEmail(email);
        userInfo.setPassword(bCryptPasswordEncoder.encode(UUID.randomUUID().toString()));
        userInfo.setAvatarUrl(pictureUrl);
        userInfo.setIsActive(true);
        userInfo.setCreatedAt(new Date());
        userInfo.setRoleId(roleService.getUserRoleByName("ROLE_READER"));
        userInfo = userInfoService.addUser(userInfo);

        Reader reader = new Reader();
        reader.setUserId(userInfo);
        readerService.addReader(reader);
      }

      UserProvider userProvider = new UserProvider();
      userProvider.setProviderId(googleId);
      userProvider.setProviderType("GOOGLE");

      Map<String, Object> providerData = new HashMap<>();
      providerData.put("email", email);
      providerData.put("name", name);
      providerData.put("picture", pictureUrl);

      userProvider.setProviderData(objectMapper.writeValueAsString(providerData));
      userProvider.setUserId(userInfo);
      userProvider.setCreatedAt(new Date());
      userProviderRepository.save(userProvider);
    }

    return userInfo;
  }
}
