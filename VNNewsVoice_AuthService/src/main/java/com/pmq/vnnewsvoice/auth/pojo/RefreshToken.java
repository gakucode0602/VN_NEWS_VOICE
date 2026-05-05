package com.pmq.vnnewsvoice.auth.pojo;

import jakarta.persistence.*;
import java.util.Date;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "refresh_token")
@Getter
@Setter
@NoArgsConstructor
public class RefreshToken {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(nullable = false, unique = true)
  private String token;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "user_id", nullable = false)
  private UserInfo userId;

  @Column(name = "expires_at", nullable = false)
  @Temporal(TemporalType.TIMESTAMP)
  private Date expiresAt;

  @Column(name = "is_revoked", nullable = false)
  private boolean revoked = false;

  @Column(name = "created_at", nullable = false)
  @Temporal(TemporalType.TIMESTAMP)
  private Date createdAt;
}
