package com.pmq.vnnewsvoice.auth.facade.impl;

import com.pmq.vnnewsvoice.auth.dto.ApiResult;
import com.pmq.vnnewsvoice.auth.dto.AuthRequest;
import com.pmq.vnnewsvoice.auth.dto.AuthResponse;
import com.pmq.vnnewsvoice.auth.dto.GoogleLoginDto;
import com.pmq.vnnewsvoice.auth.dto.GoogleLoginResponse;
import com.pmq.vnnewsvoice.auth.dto.GoogleLoginUserResponse;
import com.pmq.vnnewsvoice.auth.dto.ReaderDto;
import com.pmq.vnnewsvoice.auth.dto.RegisterReaderDto;
import com.pmq.vnnewsvoice.auth.facade.ApiAuthFacade;
import com.pmq.vnnewsvoice.auth.mapper.ReaderMapper;
import com.pmq.vnnewsvoice.auth.pojo.Reader;
import com.pmq.vnnewsvoice.auth.pojo.RefreshToken;
import com.pmq.vnnewsvoice.auth.pojo.UserInfo;
import com.pmq.vnnewsvoice.auth.service.GoogleAuthService;
import com.pmq.vnnewsvoice.auth.service.ReaderService;
import com.pmq.vnnewsvoice.auth.service.RefreshTokenService;
import com.pmq.vnnewsvoice.auth.service.RoleService;
import com.pmq.vnnewsvoice.auth.service.UserDetailService;
import com.pmq.vnnewsvoice.auth.service.UserInfoService;
import com.pmq.vnnewsvoice.auth.utils.JwtUtils;
import java.io.IOException;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ApiAuthFacadeImpl implements ApiAuthFacade {
  private final UserInfoService userInfoService;
  private final UserDetailService userDetailService;
  private final ReaderService readerService;
  private final ReaderMapper readerMapper;
  private final RoleService roleService;
  private final JwtUtils jwtUtils;
  private final GoogleAuthService googleAuthService;
  private final RefreshTokenService refreshTokenService;

  @Override
  public ApiResult<ReaderDto> registerReader(RegisterReaderDto registerReaderDto)
      throws IOException {
    UserInfo userInfo = new UserInfo();
    userInfo.setUsername(registerReaderDto.getUserIdUsername());
    userInfo.setPassword(registerReaderDto.getUserIdPassword());
    userInfo.setEmail(registerReaderDto.getUserIdEmail());
    userInfo.setAvatarUrl(registerReaderDto.getUserIdAvatarUrl());
    userInfo.setBirthday(registerReaderDto.getUserIdBirthday());
    userInfo.setAddress(registerReaderDto.getUserIdAddress());
    userInfo.setPhoneNumber(registerReaderDto.getUserIdPhoneNumber());
    userInfo.setGender(registerReaderDto.getUserIdGender());
    userInfo.setAvatarPublicId(registerReaderDto.getUserIdAvatarPublicId());
    userInfo.setRoleId(roleService.getUserRoleByName("ROLE_READER"));

    UserInfo savedUserInfo = userInfoService.addUser(userInfo);

    Reader reader = new Reader();
    reader.setUserId(savedUserInfo);
    Reader savedReader = readerService.addReader(reader);

    ReaderDto readerDto = readerMapper.toDto(savedReader);
    return ApiResult.success(HttpStatus.CREATED, readerDto, "Đăng ký thành công");
  }

  @Override
  public ApiResult<AuthResponse> login(AuthRequest authRequest) {
    Optional<UserInfo> userInfoOpt = userInfoService.getUserByUsername(authRequest.getUsername());
    if (userInfoOpt.isEmpty()) {
      return ApiResult.failure(HttpStatus.UNAUTHORIZED, "Sai tên tài khoản hoặc mật khẩu");
    }
    UserInfo userInfo = userInfoOpt.get();
    if (!Boolean.TRUE.equals(userInfo.getIsActive())) {
      return ApiResult.failure(
          HttpStatus.FORBIDDEN, "Tài khoản đã bị khoá. Vui lòng liên hệ quản trị viên.");
    }
    boolean authenticated =
        userDetailService.authenticateUser(authRequest.getUsername(), authRequest.getPassword());
    if (!authenticated) {
      return ApiResult.failure(HttpStatus.UNAUTHORIZED, "Sai tên tài khoản hoặc mật khẩu");
    }

    UserDetails userDetails = userDetailService.loadUserByUsername(authRequest.getUsername());
    Authentication authentication =
        new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());

    String token = jwtUtils.generateJwtToken(authentication);
    RefreshToken refreshToken = refreshTokenService.createRefreshToken(userInfo);
    AuthResponse authResponse = new AuthResponse(token, refreshToken.getToken());
    return ApiResult.success(HttpStatus.OK, authResponse, "Đăng nhập thành công");
  }

  @Override
  public ApiResult<GoogleLoginResponse> googleLogin(GoogleLoginDto googleLoginDto) {
    try {
      UserInfo userInfo = googleAuthService.verifyGoogleToken(googleLoginDto.getTokenId());
      UserDetails userDetails = userDetailService.loadUserByUsername(userInfo.getUsername());

      Authentication authentication =
          new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());

      String token = jwtUtils.generateJwtToken(authentication);
      RefreshToken refreshToken = refreshTokenService.createRefreshToken(userInfo);
      GoogleLoginUserResponse userResponse =
          new GoogleLoginUserResponse(
              userInfo.getId(),
              userInfo.getUsername(),
              userInfo.getEmail(),
              userInfo.getAvatarUrl());

      GoogleLoginResponse response =
          new GoogleLoginResponse(token, refreshToken.getToken(), userResponse);
      return ApiResult.success(HttpStatus.OK, response);
    } catch (Exception e) {
      return ApiResult.failure(HttpStatus.UNAUTHORIZED, e.getMessage());
    }
  }

  @Override
  @Transactional
  public ApiResult<AuthResponse> refresh(String refreshToken) {
    Optional<RefreshToken> tokenOpt = refreshTokenService.validateRefreshToken(refreshToken);
    if (tokenOpt.isEmpty()) {
      return ApiResult.failure(
          HttpStatus.UNAUTHORIZED, "Refresh token không hợp lệ hoặc đã hết hạn");
    }
    RefreshToken oldToken = tokenOpt.get();
    UserInfo userInfo = oldToken.getUserId();

    if (!Boolean.TRUE.equals(userInfo.getIsActive())) {
      return ApiResult.failure(
          HttpStatus.FORBIDDEN, "Tài khoản đã bị khoá. Vui lòng liên hệ quản trị viên.");
    }

    // Token rotation: createRefreshToken already revokes all user tokens internally,
    // so revokeRefreshToken is not needed separately.
    RefreshToken newRefreshToken = refreshTokenService.createRefreshToken(userInfo);

    UserDetails userDetails = userDetailService.loadUserByUsername(userInfo.getUsername());
    Authentication auth =
        new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
    String newAccessToken = jwtUtils.generateJwtToken(auth);

    return ApiResult.success(
        HttpStatus.OK,
        new AuthResponse(newAccessToken, newRefreshToken.getToken()),
        "Token mới đã được cấp");
  }

  @Override
  public ApiResult<Void> logout(String refreshToken) {
    refreshTokenService.revokeRefreshToken(refreshToken);
    return ApiResult.success(HttpStatus.OK, null, "Đăng xuất thành công");
  }
}
