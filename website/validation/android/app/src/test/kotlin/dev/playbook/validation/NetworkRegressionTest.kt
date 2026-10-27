package dev.playbook.validation
import dev.playbook.validation.fixtures.ktorclient.createHttpClient
import dev.playbook.validation.fixtures.ktorresult.*
import io.ktor.client.engine.mock.*
import io.ktor.client.request.*
import io.ktor.http.*
import kotlinx.coroutines.*
import kotlinx.coroutines.test.runTest
import org.junit.Test
import org.junit.Assert.*

class NetworkRegressionTest {
 @Test fun transformed401MapsToAnErrorResult() = runTest {
  val client=createHttpClient(MockEngine { respond("denied", HttpStatusCode.Unauthorized) },"https://example.test/"){ null }
  try {
   val result=safeApiCall { client.get("products") }
   assertTrue(result is NetworkResult.Error)
   assertEquals(401,(result as NetworkResult.Error).code)
   assertEquals("denied",result.errorBody)
  } finally { client.close() }
 }
 @Test fun nonIdempotentPostIsNotReplayed() = runTest {
  var calls=0
  val client=createHttpClient(MockEngine { calls++;respond("later", HttpStatusCode.ServiceUnavailable) },"https://example.test/"){ null }
  try { assertTrue(safeApiCall { client.post("order") } is NetworkResult.Error); assertEquals(1,calls) }
  finally { client.close() }
 }
 @Test fun successfulGetIsNotRetried() = runTest {
  var calls=0
  val client=createHttpClient(MockEngine { calls++;respond("ok") },"https://example.test/"){ null }
  try { assertTrue(safeApiCall { client.get("products") } is NetworkResult.Success);assertEquals(1,calls) }
  finally { client.close() }
 }
 @Test fun cancellationIsNotConvertedToAnApplicationError() = runTest {
  try { safeApiCall<Unit> { throw CancellationException("cancelled") };fail("must cancel") }
  catch(expected:CancellationException) { assertEquals("cancelled",expected.message) }
 }
}
