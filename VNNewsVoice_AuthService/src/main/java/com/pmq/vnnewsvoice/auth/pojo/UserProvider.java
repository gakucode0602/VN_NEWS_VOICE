package com.pmq.vnnewsvoice.auth.pojo;

import jakarta.persistence.*;
import java.io.Serializable;
import java.util.Date;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "userprovider")
@Getter
@Setter
@NoArgsConstructor
public class UserProvider implements Serializable {

  private static final long serialVersionUID = 1L;

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id")
  private Long id;

  @Column(name = "provider_id", nullable = false)
  private String providerId;

  @Column(name = "provider_type", nullable = false)
  private String providerType;

  @Lob
  @Column(name = "provider_data", columnDefinition = "jsonb")
  @JdbcTypeCode(SqlTypes.JSON)
  private Object providerData;

  @Column(name = "created_at")
  @Temporal(TemporalType.TIMESTAMP)
  private Date createdAt;

  @JoinColumn(name = "user_id", referencedColumnName = "id")
  @ManyToOne(optional = false)
  private UserInfo userId;

  public UserProvider(Long id) {
    this.id = id;
  }
}
