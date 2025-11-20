import bcrypt

def password_hash(password):
  return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def password_check(password, hashed):
  return bcrypt.checkpw(password.encode(), hashed.encode())