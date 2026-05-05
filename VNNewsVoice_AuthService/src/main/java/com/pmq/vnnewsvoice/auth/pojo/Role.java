package com.pmq.vnnewsvoice.auth.pojo;

import jakarta.persistence.*;
import java.io.Serializable;
import java.util.Set;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "role")
@Getter
@Setter
@NoArgsConstructor
public class Role implements Serializable {

  private static final long serialVersionUID = 1L;

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id")
  private Long id;

  @Column(name = "name", nullable = false)
  private String name;

  @OneToMany(cascade = CascadeType.ALL, mappedBy = "roleId")
  private Set<NotificationRole> notificationRoleSet;

  @OneToMany(mappedBy = "roleId")
  private Set<UserInfo> userInfoSet;

  public Role(Long id) {
    this.id = id;
  }

  public Role(Long id, String name) {
    this.id = id;
    this.name = name;
  }
}
