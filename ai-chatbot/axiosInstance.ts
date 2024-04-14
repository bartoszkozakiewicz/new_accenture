import axios from 'axios'

export const axiosInstance = axios.create({
  timeout: 10000
  //   withCredentials: true,
  // headers: {
  //   Cookie: `refreshToken=${refreshToken}; accessToken=${accessToken}`,
  // },
})
