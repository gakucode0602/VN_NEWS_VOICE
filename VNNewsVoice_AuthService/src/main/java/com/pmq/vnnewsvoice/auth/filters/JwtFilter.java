package com.pmq.vnnewsvoice.auth.filters;

import com.pmq.vnnewsvoice.auth.config.RestAuthenticationEntryPoint;
import com.pmq.vnnewsvoice.auth.service.UserDetailService;
import com.pmq.vnnewsvoice.auth.utils.JwtUtils;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
@RequiredArgsConstructor
public class JwtFilter extends OncePerRequestFilter {

  private final JwtUtils jwtUtils;
  private final UserDetailService userDetailService;
  private final RestAuthenticationEntryPoint authenticationEntryPoint;

  @Override
  protected void doFilterInternal(
      HttpServletRequest request,
      jakarta.servlet.http.HttpServletResponse response,
      FilterChain filterChain)
      throws ServletException, IOException {

    String header = request.getHeader("Authorization");

    // Passive mode: If no token, skip validation and let Spring Security handle access control.
    if (header == null || !header.startsWith("Bearer ")) {
      filterChain.doFilter(request, response);
      return;
    }

    String token = header.substring(7);
    if (!jwtUtils.validateJwtToken(token)) {
      authenticationEntryPoint.commence(request, response, null);
      return;
    }

    String username = jwtUtils.getUserNameFromJwtToken(token);
    if (username == null) {
      authenticationEntryPoint.commence(request, response, null);
      return;
    }

    try {
      UserDetails userDetails = userDetailService.loadUserByUsername(username);
      UsernamePasswordAuthenticationToken auth =
          new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
      SecurityContextHolder.getContext().setAuthentication(auth);
    } catch (Exception e) {
      authenticationEntryPoint.commence(request, response, null);
      return;
    }

    filterChain.doFilter(request, response);
  }
}
