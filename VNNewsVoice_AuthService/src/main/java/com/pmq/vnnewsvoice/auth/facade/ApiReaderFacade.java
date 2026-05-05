package com.pmq.vnnewsvoice.auth.facade;

import com.pmq.vnnewsvoice.auth.dto.ApiResult;
import com.pmq.vnnewsvoice.auth.dto.ReaderDto;
import com.pmq.vnnewsvoice.auth.pojo.CustomUserDetails;
import java.util.Map;
import org.springframework.web.multipart.MultipartFile;

public interface ApiReaderFacade {
  ApiResult<ReaderDto> getProfile(CustomUserDetails principal);

  ApiResult<Void> updateProfile(
      String username,
      String email,
      String birthdayStr,
      String gender,
      String phoneNumber,
      String address,
      MultipartFile avatar,
      CustomUserDetails principal);

  ApiResult<Void> changePassword(Map<String, String> params, CustomUserDetails principal);
}
