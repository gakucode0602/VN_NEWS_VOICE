package com.pmq.vnnewsvoice.auth.config;

import com.pmq.vnnewsvoice.auth.filters.JwtFilter;
import java.util.List;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@EnableTransactionManagement
public class SecurityConfig {

  @Bean
  public BCryptPasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
  }

  @Bean
  public SecurityFilterChain securityFilterChain(
      HttpSecurity http, JwtFilter jwtFilter, RestAccessDeniedHandler accessDeniedHandler)
      throws Exception {
    http.cors(cors -> cors.configurationSource(corsConfigurationSource()))
        .sessionManagement(
            session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class)
        .exceptionHandling(ex -> ex.accessDeniedHandler(accessDeniedHandler))
        .authorizeHttpRequests(
            auth ->
                auth
                    // Public auth endpoints
                    .requestMatchers(
                        "/api/user/login",
                        "/api/user/register",
                        "/api/user/google-login",
                        "/api/auth/refresh",
                        "/api/auth/logout",
                        "/api/.well-known/jwks.json")
                    .permitAll()
                    // Actuator health check
                    .requestMatchers("/actuator/health")
                    .permitAll()
                    // Everything else requires authentication
                    .anyRequest()
                    .authenticated())
        .csrf(csrf -> csrf.disable())
        .httpBasic(httpBasic -> httpBasic.disable());

    return http.build();
  }

  @Bean
  public CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration config = new CorsConfiguration();
    config.setAllowedOriginPatterns(
        List.of(
            "http://localhost:*",
            "http://127.0.0.1:*",
            "https://vnnewsvoice-frontend-user.vercel.app",
            "https://vnnewsvoice-frontend-admin.vercel.app"));
    config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
    config.setAllowedHeaders(
        List.of("Authorization", "Content-Type", "Content-Length", "Accept", "X-Requested-With"));
    config.setExposedHeaders(List.of("Authorization"));
    config.setAllowCredentials(true);

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/**", config);
    return source;
  }
}
