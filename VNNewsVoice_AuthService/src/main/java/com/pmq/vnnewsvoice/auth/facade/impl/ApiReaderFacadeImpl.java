package com.pmq.vnnewsvoice.auth.facade.impl;

import com.pmq.vnnewsvoice.auth.dto.ApiResult;
import com.pmq.vnnewsvoice.auth.dto.ReaderDto;
import com.pmq.vnnewsvoice.auth.facade.ApiReaderFacade;
import com.pmq.vnnewsvoice.auth.mapper.ReaderMapper;
import com.pmq.vnnewsvoice.auth.pojo.CustomUserDetails;
import com.pmq.vnnewsvoice.auth.pojo.Reader;
import com.pmq.vnnewsvoice.auth.pojo.UserInfo;
import com.pmq.vnnewsvoice.auth.service.ReaderService;
import com.pmq.vnnewsvoice.auth.service.UserInfoService;
import com.pmq.vnnewsvoice.auth.service.UserProviderService;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Map;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
@RequiredArgsConstructor
public class ApiReaderFacadeImpl implements ApiReaderFacade {
  private final UserProviderService userProviderService;
  private final BCryptPasswordEncoder passwordEncoder;
  private final ReaderService readerService;
  private final UserInfoService userInfoService;
  private final ReaderMapper readerMapper;

  @Override
  public ApiResult<ReaderDto> getProfile(CustomUserDetails principal) {
    Optional<UserInfo> userInfo = userInfoService.getUserById(principal.getUserInfo().getId());
    if (userInfo.isEmpty()) {
      return ApiResult.failure(HttpStatus.UNAUTHORIZED, "Không tìm thấy người dùng");
    }

    Optional<Reader> reader = readerService.getReaderById(userInfo.get().getReader().getId());
    if (reader.isEmpty()) {
      return ApiResult.failure(HttpStatus.UNAUTHORIZED, "Không tìm thấy độc giả");
    }

    ReaderDto readerDto = readerMapper.toDto(reader.get());
    return ApiResult.success(HttpStatus.OK, readerDto);
  }

  @Override
  public ApiResult<Void> updateProfile(
      String username,
      String email,
      String birthdayStr,
      String gender,
      String phoneNumber,
      String address,
      MultipartFile avatar,
      CustomUserDetails principal) {
    Optional<Reader> reader =
        readerService.getReaderById(principal.getUserInfo().getReader().getId());
    if (reader.isEmpty()) {
      return ApiResult.failure(HttpStatus.UNAUTHORIZED, "Không tìm thấy độc giả");
    }

    reader.get().getUserId().setUsername(username);
    reader.get().getUserId().setAvatarFile(avatar);
    reader.get().getUserId().setPhoneNumber(phoneNumber);
    reader.get().getUserId().setGender(gender);
    reader.get().getUserId().setAddress(address);

    if (birthdayStr != null && !birthdayStr.isEmpty()) {
      try {
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd");
        Date birthday = dateFormat.parse(birthdayStr);
        reader.get().getUserId().setBirthday(birthday);
      } catch (ParseException e) {
        return ApiResult.failure(
            HttpStatus.BAD_REQUEST, "Sai định dạng ngày. Định dạng yyyy-MM-dd");
      }
    }

    try {
      boolean updated = userInfoService.updateUser(reader.get().getUserId());
      if (!updated) {
        return ApiResult.failure(HttpStatus.INTERNAL_SERVER_ERROR, "Không thể cập nhật thông tin");
      }
    } catch (Exception e) {
      return ApiResult.failure(HttpStatus.INTERNAL_SERVER_ERROR, "Không thể cập nhật thông tin");
    }

    return ApiResult.success(HttpStatus.OK, null, "Cập nhật thành công");
  }

  @Override
  public ApiResult<Void> changePassword(Map<String, String> params, CustomUserDetails principal) {
    Optional<Reader> existingReader =
        readerService.getReaderById(principal.getUserInfo().getReader().getId());
    if (existingReader.isEmpty()) {
      return ApiResult.failure(HttpStatus.UNAUTHORIZED, "Không tìm thấy độc giả");
    }

    boolean isGoogleUser = userProviderService.isGoogleUser(principal.getUserInfo().getId());
    if (isGoogleUser) {
      return ApiResult.failure(
          HttpStatus.BAD_REQUEST, "Tài khoản Google không thể thay đổi mật khẩu trực tiếp");
    }

    String newPassword = params.get("newPassword");
    if (newPassword == null || newPassword.isEmpty()) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Mật khẩu mới không được để trống");
    }

    try {
      UserInfo userInfo = existingReader.get().getUserId();
      userInfo.setPassword(passwordEncoder.encode(newPassword));
      boolean updated = userInfoService.updateUser(userInfo);
      if (updated) {
        return ApiResult.success(HttpStatus.OK, null, "Đổi mật khẩu thành công");
      }
      return ApiResult.failure(HttpStatus.INTERNAL_SERVER_ERROR, "Không thể cập nhật mật khẩu");
    } catch (Exception e) {
      return ApiResult.failure(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage());
    }
  }
}
