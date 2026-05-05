package com.pmq.vnnewsvoice.auth.service.impl;

import com.pmq.vnnewsvoice.auth.pojo.UserProvider;
import com.pmq.vnnewsvoice.auth.repository.UserProviderRepository;
import com.pmq.vnnewsvoice.auth.service.UserProviderService;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
@RequiredArgsConstructor
public class UserProviderServiceImpl implements UserProviderService {
  private final UserProviderRepository userProviderRepository;

  @Override
  public UserProvider addUserProvider(UserProvider userProvider) {
    if (userProvider == null) {
      return null;
    }
    return userProviderRepository.save(userProvider);
  }

  @Override
  public UserProvider getUserProviderById(Long id) {
    if (id == null || id <= 0) {
      return null;
    }
    return userProviderRepository.findById(id).orElse(null);
  }

  @Override
  public Optional<UserProvider> findByProviderAndProviderType(
      String providerId, String providerType) {
    if (providerId == null || providerType == null) {
      return Optional.empty();
    }
    return userProviderRepository.findFirstByProviderIdAndProviderType(providerId, providerType);
  }

  @Override
  public List<UserProvider> getUserProvidersByUserId(Long userId) {
    if (userId == null || userId <= 0) {
      return List.of();
    }
    return userProviderRepository.findByUserId_Id(userId);
  }

  @Override
  public boolean isGoogleUser(Long userId) {
    if (userId == null || userId <= 0) {
      return false;
    }
    return userProviderRepository.existsByUserId_IdAndProviderType(userId, "GOOGLE");
  }

  @Override
  public boolean deleteUserProvider(Long id) {
    if (id == null || id <= 0 || !userProviderRepository.existsById(id)) {
      return false;
    }
    userProviderRepository.deleteById(id);
    return true;
  }

  @Override
  public boolean deleteUserProviderByUserId(Long userId) {
    if (userId == null || userId <= 0) {
      return false;
    }
    long deleted = userProviderRepository.deleteByUserId_Id(userId);
    return deleted > 0;
  }
}
