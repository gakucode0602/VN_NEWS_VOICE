package com.pmq.vnnewsvoice.auth.config;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;

@Component
public class RestAuthenticationEntryPoint implements AuthenticationEntryPoint {

  @Override
  public void commence(
      HttpServletRequest request,
      HttpServletResponse response,
      AuthenticationException authException)
      throws IOException {
    writeJsonError(response, HttpStatus.UNAUTHORIZED, "Unauthorized");
  }

  private void writeJsonError(HttpServletResponse response, HttpStatus status, String message)
      throws IOException {
    response.setStatus(status.value());
    response.setContentType("application/json");
    response.setCharacterEncoding("UTF-8");
    String body =
        String.format(
            "{\"success\":false,\"code\":%d,\"message\":\"%s\",\"result\":null}",
            status.value(), message);
    response.getWriter().write(body);
  }
}
