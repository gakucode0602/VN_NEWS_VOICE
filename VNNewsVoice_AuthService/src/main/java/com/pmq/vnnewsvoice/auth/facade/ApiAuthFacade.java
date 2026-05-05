package com.pmq.vnnewsvoice.auth.facade;

import com.pmq.vnnewsvoice.auth.dto.ApiResult;
import com.pmq.vnnewsvoice.auth.dto.AuthRequest;
import com.pmq.vnnewsvoice.auth.dto.AuthResponse;
import com.pmq.vnnewsvoice.auth.dto.GoogleLoginDto;
import com.pmq.vnnewsvoice.auth.dto.GoogleLoginResponse;
import com.pmq.vnnewsvoice.auth.dto.ReaderDto;
import com.pmq.vnnewsvoice.auth.dto.RegisterReaderDto;
import java.io.IOException;

public interface ApiAuthFacade {
  ApiResult<ReaderDto> registerReader(RegisterReaderDto registerReaderDto) throws IOException;

  ApiResult<AuthResponse> login(AuthRequest authRequest);

  ApiResult<GoogleLoginResponse> googleLogin(GoogleLoginDto googleLoginDto);

  ApiResult<AuthResponse> refresh(String refreshToken);

  ApiResult<Void> logout(String refreshToken);
}
