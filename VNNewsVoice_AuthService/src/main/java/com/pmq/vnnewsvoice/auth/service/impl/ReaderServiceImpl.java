package com.pmq.vnnewsvoice.auth.service.impl;

import com.pmq.vnnewsvoice.auth.pojo.Reader;
import com.pmq.vnnewsvoice.auth.pojo.UserProvider;
import com.pmq.vnnewsvoice.auth.repository.ReaderRepository;
import com.pmq.vnnewsvoice.auth.service.ReaderService;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ReaderServiceImpl implements ReaderService {
  private final ReaderRepository readerRepository;

  @Override
  @Transactional
  public Reader addReader(Reader reader) {
    if (reader == null || reader.getUserId() == null) {
      throw new IllegalArgumentException("Invalid reader data");
    }
    return readerRepository.save(reader);
  }

  @Override
  public Optional<Reader> getReaderById(Long id) {
    if (id == null) {
      return Optional.empty();
    }
    return readerRepository.findById(id);
  }

  @Override
  public Optional<Reader> getReaderByUsername(String username) {
    if (username == null || username.isEmpty()) {
      return Optional.empty();
    }
    return readerRepository.findFirstByUserId_Username(username);
  }

  @Override
  public Optional<Reader> getReaderByEmail(String email) {
    if (email == null || email.isEmpty()) {
      return Optional.empty();
    }
    return readerRepository.findFirstByUserId_Email(email);
  }

  @Override
  public Optional<Reader> getReaderByUserId(Long userId) {
    if (userId == null) {
      return Optional.empty();
    }
    return readerRepository.findFirstByUserId_Id(userId);
  }

  @Override
  public Reader getReaderByUserProvider(UserProvider userProvider) {
    if (userProvider == null || userProvider.getId() == null) {
      return null;
    }
    return readerRepository.findFirstByUserProviderId(userProvider.getId()).orElse(null);
  }
}
