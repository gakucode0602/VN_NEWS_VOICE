import type { ChangeEvent, FocusEvent } from "react";
import { useState } from "react";

type FormValues = Record<string, string>;
type FormErrors<T> = Partial<Record<keyof T, string>>;
type FormTouched<T> = Partial<Record<keyof T, boolean>>;

const useFormValidation = <T extends FormValues>(initialValues: T) => {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<FormErrors<T>>({});
  const [touched, setTouched] = useState<FormTouched<T>>({});

  const handleChange = (
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = event.target;
    setValues({
      ...values,
      [name]: value,
    });

    if (errors[name as keyof T]) {
      setErrors({
        ...errors,
        [name]: "",
      });
    }
  };

  const handleBlur = (
    event: FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name } = event.target;
    setTouched({
      ...touched,
      [name]: true,
    });

    validateField(name, values[name]);
  };

  const validateField = (name: string, value: string) => {
    let error = "";

    switch (name) {
      case "username":
        if (!value) error = "Tên đăng nhập là bắt buộc";
        else if (value.length < 3)
          error = "Tên đăng nhập phải có ít nhất 3 ký tự";
        break;
      case "password":
        if (!value) error = "Mật khẩu là bắt buộc";
        else if (value.length < 3)
          error = "Mật khẩu phải có ít nhất 3 ký tự";
        else if (!/\d/.test(value)) error = "Mật khẩu phải chứa ít nhất 1 số";
        break;
      case "email":
        if (!value) error = "Email là bắt buộc";
        else if (!/\S+@\S+\.\S+/.test(value)) error = "Email không hợp lệ";
        break;
      default:
        break;
    }

    setErrors((prev) => ({
      ...prev,
      [name]: error,
    }));

    return !error;
  };

  const validateForm = () => {
    let isValid = true;
    const newTouched: FormTouched<T> = {};

    Object.keys(values).forEach((name) => {
      newTouched[name as keyof T] = true;
      const isFieldValid = validateField(name, values[name]);
      if (!isFieldValid) isValid = false;
    });

    setTouched(newTouched);
    return isValid;
  };

  const reset = () => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  };

  return {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    validateForm,
    reset,
    setValues,
  };
};

export default useFormValidation;
