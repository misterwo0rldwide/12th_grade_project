/*
 * protocol.c - Format messaages for protocol
 *
 *              Omer Kfir (C)
 */

#include "protocol.h"
#include "headers.h"
#include "transmission.h"
#include "workqueue.h"

#include <linux/stdarg.h> // Handling unkown amount of arguments

/* Formats a message by protocol */
int protocol_format(char *dst, const char *format, ...) {
  va_list args;
  int ret_len; // Ret value of length or error

  va_start(args, format);                     // Initialize args
  ret_len = vsnprintf(NULL, 0, format, args); // Calculate message length
  va_end(args); // Close args since it was iterated by vsnprintf

  // Check for overflow
  if (ret_len + SIZE_OF_SIZE >= BUFFER_SIZE)
    return -ENOMEM;

  // Copy first length of message before actual message and pad with zeros
  snprintf(dst, SIZE_OF_SIZE + 1, "%04d", ret_len);
  ret_len += SIZE_OF_SIZE; // Ret len is the whole size of the buffer

  // Now add actual formatted string
  va_start(args, format);
  vsnprintf(dst + SIZE_OF_SIZE, BUFFER_SIZE - SIZE_OF_SIZE, format, args);
  va_end(args);

  return ret_len;
}

/* Send message with formatted message */
int protocol_send_message(bool encrypt, const char *format, ...) {
  char msg_buf[BUFFER_SIZE];
  int msg_length;
  va_list args;

  va_start(args, format);

  char fmt_buf[BUFFER_SIZE];
  vsnprintf(fmt_buf, BUFFER_SIZE, format, args);
  va_end(args);

  // Now call protocol_format with the formatted string
  msg_length = protocol_format(msg_buf, "%s", fmt_buf);

  if (msg_length > 0)
    workqueue_message(transmit_data, msg_buf, msg_length, encrypt);

  return 0;
}