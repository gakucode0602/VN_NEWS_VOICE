package com.pmq.vnnewsvoice.auth.service;

import com.pmq.vnnewsvoice.auth.pojo.UserProvider;
import java.util.List;
import java.util.Optional;

public interface UserProviderService {
  UserProvider addUserProvider(UserProvider userProvider);

  UserProvider getUserProviderById(Long id);

  Optional<UserProvider> findByProviderAndProviderType(String providerId, String providerType);

  List<UserProvider> getUserProvidersByUserId(Long userId);

  boolean isGoogleUser(Long userId);

  boolean deleteUserProvider(Long id);

  boolean deleteUserProviderByUserId(Long userId);
}
