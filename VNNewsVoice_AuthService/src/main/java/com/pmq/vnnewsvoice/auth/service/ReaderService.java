package com.pmq.vnnewsvoice.auth.service;

import com.pmq.vnnewsvoice.auth.pojo.Reader;
import com.pmq.vnnewsvoice.auth.pojo.UserProvider;
import java.util.Optional;

public interface ReaderService {
  Reader addReader(Reader reader);

  Optional<Reader> getReaderById(Long id);

  Optional<Reader> getReaderByUsername(String username);

  Optional<Reader> getReaderByEmail(String email);

  Optional<Reader> getReaderByUserId(Long userId);

  Reader getReaderByUserProvider(UserProvider userProvider);
}
