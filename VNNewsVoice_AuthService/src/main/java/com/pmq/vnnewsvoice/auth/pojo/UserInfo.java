package com.pmq.vnnewsvoice.auth.pojo;

import jakarta.persistence.*;
import java.io.Serializable;
import java.util.Date;
import java.util.Set;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.multipart.MultipartFile;

@Entity
@Table(name = "userinfo")
@Getter
@Setter
@NoArgsConstructor
public class UserInfo implements Serializable {

  private static final long serialVersionUID = 1L;

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id")
  private Long id;

  @Column(name = "username", nullable = false)
  private String username;

  @Column(name = "password", nullable = false)
  private String password;

  @Column(name = "avatar_url")
  private String avatarUrl;

  @Column(name = "email", nullable = false)
  private String email;

  @Column(name = "created_at")
  @Temporal(TemporalType.TIMESTAMP)
  private Date createdAt;

  @Column(name = "birthday")
  @Temporal(TemporalType.DATE)
  @DateTimeFormat(pattern = "yyyy-MM-dd")
  private Date birthday;

  @Column(name = "is_active")
  private Boolean isActive;

  @Column(name = "address")
  private String address;

  @Column(name = "phone_number")
  private String phoneNumber;

  @Column(name = "gender")
  private String gender;

  @Column(name = "avatar_public_id")
  private String avatarPublicId;

  @Column(name = "first_name")
  private String firstName;

  @Column(name = "last_name")
  private String lastName;

  @JoinColumn(name = "role_id", referencedColumnName = "id")
  @ManyToOne(fetch = FetchType.EAGER)
  private Role roleId;

  @OneToOne(cascade = CascadeType.ALL, mappedBy = "userId", fetch = FetchType.LAZY)
  private Admin admin;

  @OneToOne(cascade = CascadeType.ALL, mappedBy = "userId", fetch = FetchType.LAZY)
  private Reader reader;

  @OneToMany(cascade = CascadeType.ALL, mappedBy = "userId")
  private Set<Notification> notificationSet;

  @OneToMany(cascade = CascadeType.ALL, mappedBy = "userId")
  private Set<UserProvider> userProviderSet;

  @Transient private MultipartFile avatarFile;

  public UserInfo(Long id) {
    this.id = id;
  }
}
